#![no_std]
#![no_main]
#![feature(abi_x86_interrupt)]

use core::panic::PanicInfo;
extern crate alloc;

use alloc::{boxed::Box, vec, vec::Vec, rc::Rc};
use bootloader_api::{entry_point, BootInfo};
use x86_64::VirtAddr;

static HELLO: &[u8] = b"AgentOS: hello from kernel (Bootloader 0.11)";

const CONFIG: bootloader_api::BootloaderConfig = {
    let mut config = bootloader_api::BootloaderConfig::new_default();
    config.mappings.physical_memory = Some(bootloader_api::config::Mapping::Dynamic);
    config
};

entry_point!(kernel_main, config = &CONFIG);

mod gdt;
mod interrupts;
mod serial;
mod screen;
mod memory;
mod allocator;
mod fs;
mod task;
mod agent;

use task::{Task, executor::SimpleExecutor};


fn kernel_main(boot_info: &'static mut BootInfo) -> ! {
    // ... (Init code remains) ...
    // 1. Serial Debug
    serial_println!("AgentOS: serial debug start (0.11)");

    // 2. Initialize Core Systems
    gdt::init();
    interrupts::init_idt();
    unsafe { interrupts::PICS.lock().initialize() };
    x86_64::instructions::interrupts::enable();

    serial_println!("AgentOS: interrupts enabled");
    
    // 3. Initialize Memory & Heap
    let phys_mem_offset = VirtAddr::new(boot_info.physical_memory_offset.into_option().unwrap());
    let mut mapper = unsafe { memory::init(phys_mem_offset) };
    let mut frame_allocator = unsafe {
        memory::BootInfoFrameAllocator::init(&boot_info.memory_regions)
    };

    allocator::init_heap(&mut mapper, &mut frame_allocator)
        .expect("heap initialization failed");

    // 4. Framebuffer output (Global Init)
    if let Some(framebuffer) = boot_info.framebuffer.as_mut() {
        let info = framebuffer.info();
        let buffer = framebuffer.buffer_mut();
        screen::init(buffer, info);
    }
    
    // Clear & Logo
    use crate::screen::WRITER;
    use core::fmt::Write; // Import Write trait for `write!` and `writeln!`
    x86_64::instructions::interrupts::without_interrupts(|| {
        if let Some(writer) = WRITER.lock().as_mut() {
            writer.clear();
            
            // Draw Logo logic repeated for consistent look, but using global writer
            let screen_width = writer.width();
            let screen_height = writer.height();
            let logo_scale = 3; 
            let logo_width = 9 * 8 * logo_scale; 
            let x_center = if screen_width > logo_width { (screen_width - logo_width) / 2 } else { 0 };
            let y_center = screen_height / 3;

            writer.set_cursor(x_center, y_center);
            writer.set_scale(logo_scale);
            writer.set_color(0, 255, 255); 
            let _ = write!(writer, "Qai ");
            writer.set_color(255, 0, 255); 
            let _ = writeln!(writer, "AgentOS");
            
            // Developer Name
            let dev_scale = 1;
            let dev_text = "Developer: Karan Chandra Dey";
            let dev_width = dev_text.len() * 8 * dev_scale;
            let dev_x = if screen_width > dev_width { (screen_width - dev_width) / 2 } else { 0 };
            let dev_y = y_center + (16 * logo_scale) + 10; // Below title

            writer.set_cursor(dev_x, dev_y);
            writer.set_scale(dev_scale);
            writer.set_color(0, 255, 0); // Green color
            let _ = writeln!(writer, "{}", dev_text);

            let divider_y = writer.height() / 3 + (8 * logo_scale) + 40;
            writer.set_cursor(screen_width / 4, divider_y);
            writer.set_scale(1);
            writer.set_color(100, 100, 100); 
            for _ in 0..(screen_width / 2 / 8) {
                let _ = write!(writer, "-");
            }
            
            // Reset to default for shell
            writer.set_cursor(0, divider_y + 60);
            writer.set_scale(1);
            writer.set_color(255, 255, 255);
        }
    });

    println!("\n\nInitialized Global Screen Writer.");

    // 5. Run Executor
    serial_println!("AgentOS: initializing agent subsys");
    fs::init();
    agent::init();

    let mut executor = SimpleExecutor::new();
    executor.spawn(Task::new(agent::AgentDaemon::new().run()));
    executor.spawn(Task::new(task::shell::run()));
    serial_println!("AgentOS: running executor");
    executor.run();
    
    // Should not return, but satisfy type checker
    loop {
        x86_64::instructions::hlt();
    }
}

#[panic_handler]
fn panic(info: &PanicInfo) -> ! {
    serial_println!("{}", info);
    loop {}
}
