use std::{env, process::{Command, Stdio}, path::PathBuf, io::{BufRead, BufReader, Write}, fs::File, thread};
use bootloader::BiosBoot;

fn main() {
    let mut args = env::args().skip(1); // Skip executable name
    let kernel_binary = args.next().expect("usage: builder <kernel-executable>");
    let kernel_path = PathBuf::from(kernel_binary);

    // Create BIOS disk image
    let bios = BiosBoot::new(&kernel_path);
    let disk_image = kernel_path.with_extension("img");
    bios.create_disk_image(&disk_image).expect("failed to create BIOS disk image");

    // Run QEMU with PTY serial
    let mut qemu = Command::new("qemu-system-x86_64");
    qemu.arg("-drive").arg(format!("format=raw,file={}", disk_image.display()));
    qemu.arg("-serial").arg("pty");
    qemu.arg("-m").arg("512M"); 
    
    // Pass remaining args
    for arg in args {
        qemu.arg(arg);
    }

    // Capture stderr to get PTY path
    qemu.stderr(Stdio::piped());
    
    let mut child = qemu.spawn().expect("failed to spawn qemu");
    
    // Read stderr in a separate thread so we don't block
    let stderr = child.stderr.take().expect("failed to get stderr");
    let stderr_thread = thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line in reader.lines() {
            if let Ok(line) = line {
                eprintln!("{}", line); // Pass through to terminal
                
                // Look for "char device redirected to /dev/ttysXXX"
                if line.contains("char device redirected to") {
                    if let Some(start) = line.find("/dev/") {
                        let pty_path = &line[start..];
                        // Remove any trailing text after the path
                        let pty_path: &str = pty_path.split_whitespace().next().unwrap_or(pty_path);
                        
                        // Save to file for bridge to read
                        let pty_file = PathBuf::from("pty_device.txt");
                        if let Ok(mut f) = File::create(&pty_file) {
                            let _ = writeln!(f, "{}", pty_path);
                            eprintln!("PTY path saved to: {:?}", pty_file);
                        }
                    }
                }
            }
        }
    });
    
    // Wait for QEMU to exit
    let status = child.wait().expect("failed to wait for qemu");
    
    // Wait for stderr thread (it will exit when QEMU closes stderr)
    let _ = stderr_thread.join();
    
    if !status.success() {
        std::process::exit(status.code().unwrap_or(1));
    }
}
