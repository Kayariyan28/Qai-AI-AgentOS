use alloc::string::String;
use alloc::vec::Vec;
use serde::{Deserialize, Serialize};
use crossbeam_queue::ArrayQueue;
use conquer_once::spin::OnceCell;
use core::future::Future;
use core::task::{Context, Poll};
use core::pin::Pin;

use crate::{serial_print, serial_println};

/// Standard message envelope for Agent communication
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct AgentMessage {
    pub id: u64,
    pub target: String, // "shell", "daemon", "tool"
    pub msg_type: String, // "request", "response", "log"
    pub content: String,
}

/// The "Device" that exposes the Agent channel to the Kernel components
pub struct AgentDevice {
    pub outbound: ArrayQueue<AgentMessage>, // Shell -> Serial
    pub inbound: ArrayQueue<AgentMessage>,  // Serial -> Shell
}

static AGENT_DEVICE: OnceCell<AgentDevice> = OnceCell::uninit();

pub fn init() {
    AGENT_DEVICE.try_init_once(|| AgentDevice {
        outbound: ArrayQueue::new(20),
        inbound: ArrayQueue::new(20),
    }).expect("AgentDevice already initialized");
}

pub fn device() -> &'static AgentDevice {
    AGENT_DEVICE.try_get().expect("AgentDevice not initialized")
}

// --- Daemon Task ---

pub struct AgentDaemon {
    rx_buffer: String,
}

impl AgentDaemon {
    pub fn new() -> Self {
        Self { rx_buffer: String::with_capacity(1024) }
    }

    pub async fn run(mut self) {
        serial_println!("Agentd: Daemon Started");
        let dev = device();

        loop {
            // 1. Process Outbound (Send to Host)
            while let Some(msg) = dev.outbound.pop() {
                if let Ok(json) = serde_json::to_string(&msg) {
                    // Debug disabled - causes feedback with PTY
                    // serial_println!("TX: {}", json);
                    // Send to serial
                    for byte in json.bytes() {
                        // Busy wait if serial is full? Or drop?
                        // For reliable comms, we should spin-wait (with timeout ideally)
                        // For now: spin (serial is fast enough usually)
                        while !crate::serial::try_send_byte(byte) {
                            YieldNow::default().await; 
                        }
                    }
                    // Send Newline delimiter
                    while !crate::serial::try_send_byte(b'\n') { 
                        YieldNow::default().await;
                    }
                }
            }

            // 2. Process Inbound (Read from Host)
            // We drain the Serial FIFO
            while let Some(byte) = crate::serial::try_read_byte() {
                // Debug: Show received byte 
                crate::print!("{}", byte as char);
                if byte == b'\n' {
                    if !self.rx_buffer.is_empty() {
                        // Attempt to parse
                        if let Ok(msg) = serde_json::from_str::<AgentMessage>(&self.rx_buffer) {
                             if msg.msg_type == "tool_call" {
                                 // Execute Tool (fs logic, same as before)
                                 let content = msg.content.clone();
                                 let result = if content.starts_with("fs_write:") {
                                     let parts: Vec<&str> = content.splitn(3, ':').collect();
                                     if parts.len() == 3 {
                                         let filename = parts[1];
                                         let data = parts[2];
                                         crate::fs::write_file(filename, data.as_bytes());
                                         String::from("OK")
                                     } else {
                                         String::from("Error: Invalid fs_write format")
                                     }
                                 } else if content.starts_with("fs_read:") {
                                     let parts: Vec<&str> = content.splitn(2, ':').collect();
                                     if parts.len() == 2 {
                                         let filename = parts[1];
                                         if let Some(data) = crate::fs::read_file(filename) {
                                              if let Ok(s) = String::from_utf8(data) {
                                                  s
                                              } else {
                                                  String::from("<Binary Data>")
                                              }
                                         } else {
                                              String::from("Error: File not found")
                                         }
                                     } else {
                                         String::from("Error: Invalid fs_read format")
                                     }
                                 } else if content.starts_with("fs_ls") {
                                     let files = crate::fs::list_dir();
                                     let mut s = String::from("Files: ");
                                     for f in files {
                                         s.push_str(&f);
                                         s.push_str(" ");
                                     }
                                     s
                                 } else {
                                     String::from("Error: Unknown Tool")
                                 };

                                 // Reply with Result
                                 let reply = AgentMessage {
                                     id: msg.id,
                                     target: String::from("host"),
                                     msg_type: String::from("tool_result"),
                                     content: result,
                                 };
                                 if let Err(_) = dev.outbound.push(reply) {
                                     serial_println!("Agentd: Outbound queue full dropping tool result");
                                 }
                             } else if msg.msg_type == "gui_plot" {
                                 crate::serial_println!("DEBUG: Received gui_plot message"); // DEBUG SERIAL
                                 // Handle GUI Plot
                                 #[derive(Deserialize)]
                                 struct GuiPlotData {
                                     title: String,
                                     x_values: Vec<f64>,
                                     y_values: Vec<f64>,
                                 }

                                 match serde_json::from_str::<GuiPlotData>(&msg.content) {
                                     Ok(plot) => {
                                         crate::serial_println!("DEBUG: Parsed Plot Data. Points: {}", plot.x_values.len());
                                         crate::screen::clear_screen();
                                         
                                         // Draw Axes
                                         let width = 800; // Hardcoded for now, ideal: screen::width()
                                         let height = 600;
                                         let margin = 50;
                                         
                                         // Draw X/Y Axis
                                         crate::screen::set_color(100, 100, 100);
                                         crate::screen::draw_line(margin, height - margin, width - margin, height - margin); // X
                                         crate::screen::draw_line(margin, margin, margin, height - margin); // Y
                                         
                                         // Draw Title
                                         crate::print!("\n  Graph: {}", plot.title);

                                         // Plot Data
                                         let min_x = plot.x_values.iter().fold(f64::INFINITY, |a, &b| a.min(b));
                                         let max_x = plot.x_values.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
                                         let min_y = plot.y_values.iter().fold(f64::INFINITY, |a, &b| a.min(b));
                                         let max_y = plot.y_values.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
                                         
                                         let range_x = if max_x - min_x == 0.0 { 1.0 } else { max_x - min_x };
                                         let range_y = if max_y - min_y == 0.0 { 1.0 } else { max_y - min_y };
                                         
                                         crate::serial_println!("DEBUG: Ranges X=[{},{}] Y=[{},{}]", min_x, max_x, min_y, max_y);

                                         let plot_w = (width - 2 * margin) as f64;
                                         let plot_h = (height - 2 * margin) as f64;
                                         
                                         crate::screen::set_color(0, 255, 0); // Green Line
                                         
                                         for i in 0..plot.x_values.len() - 1 {
                                             let x1 = plot.x_values[i];
                                             let y1 = plot.y_values[i];
                                             let x2 = plot.x_values[i+1];
                                             let y2 = plot.y_values[i+1];
                                             
                                             let sx1 = margin as f64 + (x1 - min_x) / range_x * plot_w;
                                             let sy1 = (height - margin) as f64 - (y1 - min_y) / range_y * plot_h;
                                             let sx2 = margin as f64 + (x2 - min_x) / range_x * plot_w;
                                             let sy2 = (height - margin) as f64 - (y2 - min_y) / range_y * plot_h;
                                             
                                             crate::screen::draw_line(sx1 as usize, sy1 as usize, sx2 as usize, sy2 as usize);
                                         }
                                         
                                         crate::screen::set_color(255, 255, 255); // Reset
                                         crate::serial_println!("DEBUG: Plot Drawn Complete");
                                     },
                                     Err(e) => {
                                         crate::serial_println!("DEBUG: Failed to parse plot JSON");
                                     }
                                 }
                             } else if msg.msg_type == "gui_pipeline_diagram" {
                    // Start Pipeline Diagram --------------------------
                    #[derive(Deserialize)]
                    struct PNode {
                        id: String,
                        label: String,
                        x: usize,
                        y: usize,
                        w: usize,
                        h: usize,
                        color: String,
                    }

                    #[derive(Deserialize)]
                    struct PEdge {
                        from: String,
                        to: String,
                    }

                    #[derive(Deserialize)]
                    struct PipelineData {
                        title: String,
                        nodes: Vec<PNode>,
                        edges: Vec<PEdge>,
                    }
                    
                    match serde_json::from_str::<PipelineData>(&msg.content) {
                        Ok(data) => {
                            crate::screen::clear_screen();
                            crate::screen::set_cursor(10, 10);
                            crate::screen::set_color(255, 255, 255);
                            crate::print!("PIPELINE: {}", data.title);
                            
                            // Helper to find node center
                            let get_center = |id: &str| -> Option<(usize, usize)> {
                                for n in &data.nodes {
                                    if n.id == id {
                                        return Some((n.x + n.w/2, n.y + n.h/2));
                                    }
                                }
                                None
                            };
                            
                            // 1. Draw Edges (Lines)
                            crate::screen::set_color(180, 180, 180); // Grey lines
                            for edge in &data.edges {
                                if let (Some(start), Some(end)) = (get_center(&edge.from), get_center(&edge.to)) {
                                    crate::screen::draw_line(start.0, start.1, end.0, end.1);
                                    // Draw arrowhead (simple)
                                    // ... skipped for simplicity/time, just lines for now
                                }
                            }
                            
                            // 2. Draw Nodes (Boxes)
                            for node in &data.nodes {
                                // Set Color
                                match node.color.as_str() {
                                    "red" => crate::screen::set_color(200, 50, 50),
                                    "green" => crate::screen::set_color(50, 200, 50),
                                    "blue" => crate::screen::set_color(50, 50, 200),
                                    "yellow" => crate::screen::set_color(200, 200, 50),
                                    "cyan" => crate::screen::set_color(50, 200, 200),
                                    "magenta" => crate::screen::set_color(200, 50, 200),
                                    _ => crate::screen::set_color(100, 100, 100), // Grey default
                                }
                                
                                crate::screen::fill_rect(node.x, node.y, node.w, node.h);
                                
                                // Draw Border
                                crate::screen::set_color(255, 255, 255);
                                crate::screen::draw_line(node.x, node.y, node.x+node.w, node.y);
                                crate::screen::draw_line(node.x, node.y+node.h, node.x+node.w, node.y+node.h);
                                crate::screen::draw_line(node.x, node.y, node.x, node.y+node.h);
                                crate::screen::draw_line(node.x+node.w, node.y, node.x+node.w, node.y+node.h);
                                
                                // Draw Label (Centered-ish)
                                let label_lines: Vec<&str> = node.label.split('\n').collect();
                                let line_h = 12;
                                let start_y = node.y + (node.h - (label_lines.len() * line_h)) / 2;
                                
                                for (i, line) in label_lines.iter().enumerate() {
                                    crate::screen::set_cursor(node.x + 5, start_y + (i * line_h));
                                    crate::print!("{}", line);
                                }
                            }
                        },
                        Err(e) => {
                             crate::serial_println!("DEBUG: Pipeline Parse Error");
                        }
                    }
                    // End Pipeline Diagram --------------------------
                } else if msg.msg_type == "gui_ml_dashboard" {
                                 // Handle ML Dashboard
                                 #[derive(Deserialize)]
                                 struct AccuracyChart {
                                     title: String,
                                     labels: Vec<String>,
                                     train: Vec<f64>,
                                     test: Vec<f64>,
                                 }
                                 #[derive(Deserialize)]
                                 struct ConfusionMatrix {
                                     title: String,
                                     labels: Vec<String>,
                                     grid: Vec<Vec<u32>>, 
                                 }
                                 #[derive(Deserialize)]
                                 struct GuiMlDashboardData {
                                     summary: String,
                                     accuracy_chart: AccuracyChart,
                                     confusion_matrix: ConfusionMatrix,
                                 }

                                 match serde_json::from_str::<GuiMlDashboardData>(&msg.content) {
                                     Ok(dash) => {
                                         crate::screen::clear_screen();
                                         
                                         // 1. Accuracy Chart (Top Half)
                                         // Title
                                         crate::screen::set_cursor(10, 10);
                                         crate::print!("{}", dash.accuracy_chart.title);
                                         
                                         let chart_base_y = 250;
                                         let slot_width = 150;
                                         let bar_width = 40;
                                         let start_x = 50;
                                         
                                         for (i, label) in dash.accuracy_chart.labels.iter().enumerate() {
                                             if i >= 4 { break; } // Limit to 4 models
                                             
                                             let x_base = start_x + i * slot_width;
                                             
                                             // Train Bar (Green)
                                             let train_val = dash.accuracy_chart.train.get(i).unwrap_or(&0.0);
                                             let tr_h = (*train_val * 200.0) as usize;
                                             crate::screen::set_color(0, 200, 0);
                                             crate::screen::fill_rect(x_base, chart_base_y - tr_h, bar_width, tr_h);
                                             
                                             // Test Bar (Blue)
                                             let test_val = dash.accuracy_chart.test.get(i).unwrap_or(&0.0);
                                             let te_h = (*test_val * 200.0) as usize;
                                             crate::screen::set_color(0, 0, 200);
                                             crate::screen::fill_rect(x_base + bar_width, chart_base_y - te_h, bar_width, te_h);
                                             
                                             // Label
                                             crate::screen::set_color(255, 255, 255);
                                             crate::screen::set_cursor(x_base, chart_base_y + 10);
                                             crate::print!("{}", label);
                                         }
                                         
                                         // 2. Confusion Matrix (Bottom Half)
                                         crate::screen::set_cursor(10, 300);
                                         crate::print!("{}", dash.confusion_matrix.title);
                                         
                                         let grid_start_x = 250;
                                         let grid_start_y = 350;
                                         let cell_size = 100;
                                         
                                         for (r, row) in dash.confusion_matrix.grid.iter().enumerate() {
                                             for (c, val) in row.iter().enumerate() {
                                                 // Check bounds
                                                 if r > 1 || c > 1 { continue; } // Handle binary only for now safely
                                                 
                                                 let x = grid_start_x + c * cell_size;
                                                 let y = grid_start_y + r * cell_size;
                                                 
                                                 // Intensity (Simple mapping: val * 5, capped at 255)
                                                 let intensity = ((*val as u32) * 5).min(255) as u8;
                                                 // Red shade
                                                 crate::screen::set_color(intensity, 0, 0); 
                                                 crate::screen::fill_rect(x, y, cell_size - 2, cell_size - 2);
                                                 
                                                 // Text Value
                                                 crate::screen::set_color(255, 255, 255);
                                                 crate::screen::set_cursor(x + 40, y + 45);
                                                 crate::print!("{}", val);
                                             }
                                         }
                                         
                                         // Draw Summary/Text
                                         crate::screen::set_cursor(10, 580);
                                         crate::print!("Dashboard Ready.");
                                     },
                                     Err(_) => {
                                          crate::serial_println!("DEBUG: Failed to parse Dashboard JSON");
                                     }
                                 }
                             } else if msg.msg_type == "gui_chess" {
                                 // Enhanced Chess Board GUI Handler
                                 #[derive(Deserialize, Default)]
                                 struct ChessAnalysis {
                                     winner: Option<String>,
                                     winning_margin: Option<String>,
                                     key_moves: Option<Vec<String>>,
                                     white_strategy: Option<Vec<String>>,
                                     black_strategy: Option<Vec<String>>,
                                 }
                                 
                                 #[derive(Deserialize)]
                                 struct ChessData {
                                     board: Vec<Vec<String>>,
                                     turn: String,
                                     move_count: usize,
                                     last_move: Option<String>,
                                     game_over: bool,
                                     result: Option<String>,
                                     in_check: bool,
                                     // Enhanced fields
                                     #[serde(default)]
                                     event: String,
                                     #[serde(default)]
                                     move_number: usize,
                                     #[serde(default)]
                                     player: String,
                                     #[serde(default)]
                                     reasoning: String,
                                     #[serde(default)]
                                     score: i32,
                                     #[serde(default)]
                                     analysis: Option<ChessAnalysis>,
                                 }
                                 
                                 match serde_json::from_str::<ChessData>(&msg.content) {
                                     Ok(chess) => {
                                         crate::screen::clear_screen();
                                         crate::screen::set_cursor(10, 10);
                                         
                                         // Title with decorative border
                                         crate::screen::set_color(255, 215, 0); // Gold
                                         crate::println!("╔═══════════════════════════════════╗");
                                         crate::println!("║   ♔ AI CHESS BATTLE ♚              ║");
                                         crate::println!("╚═══════════════════════════════════╝");
                                         crate::println!("");
                                         
                                         // Move info header
                                         if chess.move_number > 0 && !chess.player.is_empty() {
                                             crate::screen::set_color(100, 200, 255); // Cyan
                                             crate::print!("Move {}: ", chess.move_number);
                                             if chess.player == "White" {
                                                 crate::screen::set_color(255, 255, 255);
                                             } else {
                                                 crate::screen::set_color(180, 180, 180);
                                             }
                                             if let Some(ref m) = chess.last_move {
                                                 crate::println!("{} plays {}", chess.player, m);
                                             }
                                         }
                                         
                                         // Strategy reasoning
                                         if !chess.reasoning.is_empty() {
                                             crate::screen::set_color(200, 200, 100); // Yellow
                                             // Truncate long reasoning
                                             let reason = if chess.reasoning.len() > 40 {
                                                 &chess.reasoning[..40]
                                             } else {
                                                 &chess.reasoning
                                             };
                                             crate::println!("Strategy: {}", reason);
                                         }
                                         crate::println!("");
                                         
                                         // Board header
                                         crate::screen::set_color(150, 150, 150);
                                         crate::println!("    a   b   c   d   e   f   g   h");
                                         
                                         // Draw board with pieces
                                         for (rank, row) in chess.board.iter().enumerate() {
                                             let rank_num = 8 - rank;
                                             crate::screen::set_color(150, 150, 150);
                                             crate::print!(" {} ", rank_num);
                                             
                                             for (file, piece) in row.iter().enumerate() {
                                                 // Alternate square colors
                                                 let is_light = (rank + file) % 2 == 0;
                                                 
                                                 // Piece display
                                                 let piece_char = match piece.as_str() {
                                                     "R" => "♖", "N" => "♘", "B" => "♗", "Q" => "♕", "K" => "♔", "P" => "♙",
                                                     "r" => "♜", "n" => "♞", "b" => "♝", "q" => "♛", "k" => "♚", "p" => "♟",
                                                     _ => "·"
                                                 };
                                                 
                                                 // Color pieces
                                                 if piece.chars().next().map(|c| c.is_uppercase()).unwrap_or(false) {
                                                     crate::screen::set_color(255, 255, 255); // White pieces
                                                 } else if piece != "." {
                                                     crate::screen::set_color(200, 100, 100); // Red-ish for black
                                                 } else if is_light {
                                                     crate::screen::set_color(80, 80, 80);
                                                 } else {
                                                     crate::screen::set_color(50, 50, 50);
                                                 }
                                                 
                                                 crate::print!("{} ", piece_char);
                                             }
                                             crate::println!("");
                                         }
                                         
                                         crate::println!("");
                                         
                                         // Status bar
                                         if chess.in_check {
                                             crate::screen::set_color(255, 50, 50); // Red
                                             crate::println!("⚠  CHECK! ⚠");
                                         }
                                         
                                         // Score indicator
                                         if chess.score != 0 {
                                             crate::screen::set_color(150, 150, 150);
                                             crate::print!("Material: ");
                                             if chess.score > 0 {
                                                 crate::screen::set_color(100, 255, 100);
                                                 crate::println!("+{} (White)", chess.score);
                                             } else {
                                                 crate::screen::set_color(255, 150, 150);
                                                 crate::println!("{} (Black)", chess.score);
                                             }
                                         }
                                         
                                         // Game Over - Show Analysis
                                         if chess.game_over || chess.event == "game_end" {
                                             crate::println!("");
                                             crate::screen::set_color(255, 215, 0); // Gold
                                             crate::println!("════════════════════════════════════");
                                             crate::println!("          GAME OVER");
                                             crate::println!("════════════════════════════════════");
                                             
                                             if let Some(ref result) = chess.result {
                                                 crate::screen::set_color(255, 255, 255);
                                                 crate::println!("");
                                                 crate::println!("Result: {}", result);
                                             }
                                             
                                             // Show analysis if available
                                             if let Some(ref analysis) = chess.analysis {
                                                 crate::println!("");
                                                 
                                                 if let Some(ref winner) = analysis.winner {
                                                     crate::screen::set_color(100, 255, 100);
                                                     crate::println!("Winner: {}", winner);
                                                 }
                                                 
                                                 if let Some(ref margin) = analysis.winning_margin {
                                                     crate::screen::set_color(200, 200, 200);
                                                     crate::println!("Margin: {}", margin);
                                                 }
                                                 
                                                 // Key moves
                                                 if let Some(ref keys) = analysis.key_moves {
                                                     crate::println!("");
                                                     crate::screen::set_color(255, 200, 100);
                                                     crate::println!("Key Moves:");
                                                     for (i, km) in keys.iter().take(3).enumerate() {
                                                         crate::screen::set_color(200, 200, 200);
                                                         // Truncate long strings
                                                         let display = if km.len() > 35 { &km[..35] } else { km };
                                                         crate::println!("  {}. {}", i+1, display);
                                                     }
                                                 }
                                                 
                                                 // Winner strategy
                                                 let winner_strat = if analysis.winner.as_ref().map(|w| w.contains("White")).unwrap_or(false) {
                                                     &analysis.white_strategy
                                                 } else {
                                                     &analysis.black_strategy
                                                 };
                                                 
                                                 if let Some(ref strats) = winner_strat {
                                                     crate::println!("");
                                                     crate::screen::set_color(100, 200, 255);
                                                     crate::println!("Winning Strategy:");
                                                     for s in strats.iter().take(3) {
                                                         crate::screen::set_color(200, 200, 200);
                                                         let display = if s.len() > 35 { &s[..35] } else { s };
                                                         crate::println!("  - {}", display);
                                                     }
                                                 }
                                             }
                                         } else {
                                             // Show whose turn
                                             crate::screen::set_color(150, 255, 150);
                                             crate::println!("");
                                             crate::println!("{} to move...", chess.turn);
                                         }
                                         
                                         crate::screen::set_color(255, 255, 255);
                                     },
                                     Err(_) => {
                                         crate::serial_println!("DEBUG: Failed to parse Chess JSON");
                                     }
                                 }
                             } else {
                                 // Push to inbound (Shell)
                                 if let Err(_) = dev.inbound.push(msg) {
                                     serial_println!("Agentd: Inbound queue full, dropping message");
                                 }
                             }
                        } else {
                            // Silently discard unparseable data to prevent feedback loop
                            // serial_println!("Agentd: Parse Error: {}", self.rx_buffer);
                        }
                        self.rx_buffer.clear();
                    }
                } else {
                    self.rx_buffer.push(byte as char);
                }
            }

            // 3. Yield to allow Shell to run
            // This is a simple cooperative multitasking yield
            YieldNow::default().await;
        }
    }
}

// Helper for yielding
#[derive(Default)]
struct YieldNow {
    yielded: bool,
}

impl Future for YieldNow {
    type Output = ();

    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<()> {
        if self.yielded {
            Poll::Ready(())
        } else {
            self.yielded = true;
            cx.waker().wake_by_ref();
            Poll::Pending
        }
    }
}
