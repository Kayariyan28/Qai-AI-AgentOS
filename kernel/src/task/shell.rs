use crate::{print, println};
use super::keyboard::ScancodeStream;
use futures_util::stream::StreamExt;
use pc_keyboard::{layouts, DecodedKey, HandleControl, Keyboard, ScancodeSet1};
use alloc::string::String;
use crate::agent::{self, AgentMessage};

pub async fn run() {
    println!("\n");
    println!("  Qai AgentOS (Kernel v0.3)");
    println!("  Shell: Agentic Mode");
    println!("  -------------------------");
    println!("  Scroll: Fn+Up / Fn+Down");
    println!("  Backspace: Delete key");
    
    print!("> ");

    let mut scancodes = ScancodeStream::new();
    let mut keyboard = Keyboard::new(ScancodeSet1::new(), layouts::Us104Key,
        HandleControl::Ignore);
    
    let mut line_buffer = String::new();
    let mut req_id = 0;

    futures_util::future::poll_fn(|cx| {
        use core::task::Poll;
        use core::pin::Pin;
        use futures_util::stream::Stream;
            
        while let Poll::Ready(Some(scancode)) = Pin::new(&mut scancodes).poll_next(cx) {
            // DEBUG disabled - tools working
            // print!("[{:02x}]", scancode);
            
            // Handle scroll and delete via raw scancodes
            // For Mac in QEMU:
            // Fn+Up sends 0x48 (Arrow Up), Fn+Down sends 0x50 (Arrow Down)
            // Delete key sends 0x53
            match scancode {
                0x48 => { // Arrow Up (Fn+Up on Mac) - scroll up
                    crate::screen::scroll_up();
                    continue;
                }
                0x50 => { // Arrow Down (Fn+Down on Mac) - scroll down
                    crate::screen::scroll_down();
                    continue;
                }
                0x53 => { // Delete key - act as backspace
                    if line_buffer.pop().is_some() {
                        print!("\x08 \x08"); // Backspace, space, backspace
                    }
                    continue;
                }
                _ => {}
            }
            
            if let Ok(Some(key_event)) = keyboard.add_byte(scancode) {
                if let Some(key) = keyboard.process_keyevent(key_event) {
                    match key {
                        DecodedKey::Unicode(c) => {
                            match c {
                                '\n' => {
                                    print!("\n");
                                    if !line_buffer.is_empty() {
                                        let msg = AgentMessage {
                                            id: req_id,
                                            target: String::from("host"),
                                            msg_type: String::from("task"),
                                            content: line_buffer.clone(),
                                        };
                                        req_id += 1;
                                        
                                        if let Err(_) = agent::device().outbound.push(msg) {
                                            println!("Error: Agent queue full");
                                        } else {
                                            println!("(Sending to Agent...)");
                                        }
                                        line_buffer.clear();
                                    }
                                    print!("> ");
                                },
                                '\x08' | '\x7f' => { // Backspace or DEL
                                     if line_buffer.pop().is_some() {
                                         print!("\x08 \x08");
                                     }
                                },
                                c => {
                                    print!("{}", c);
                                    line_buffer.push(c);
                                }
                            }
                        },
                        DecodedKey::RawKey(key) => {
                            use pc_keyboard::KeyCode;
                            match key {
                                KeyCode::ArrowUp => crate::screen::scroll_up(),
                                KeyCode::ArrowDown => crate::screen::scroll_down(),
                                KeyCode::Delete => {
                                    if line_buffer.pop().is_some() {
                                        print!("\x08 \x08");
                                    }
                                }
                                _ => {}
                            }
                        }
                    }
                }
            }
        }
        
        // 2. Check Inbox (Responses from Agentd)
        let device = agent::device();
        while let Some(msg) = device.inbound.pop() {
            println!("\n\n[Agent Reply]: {}", msg.content);
            print!("\n> {}", line_buffer); // Restore prompt
        }
        
        Poll::Pending::<()>
    }).await;
}
