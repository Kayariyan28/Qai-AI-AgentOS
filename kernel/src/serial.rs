use lazy_static::lazy_static;
use spin::Mutex;
use uart_16550::SerialPort;
use x86_64::instructions::interrupts;
use core::fmt;

lazy_static! {
    pub static ref SERIAL1: Mutex<SerialPort> = {
        let mut serial_port = unsafe { SerialPort::new(0x3F8) };
        serial_port.init();
        Mutex::new(serial_port)
    };
}

#[doc(hidden)]
pub fn _print(args: fmt::Arguments) {
    interrupts::without_interrupts(|| {
        use core::fmt::Write;
        SERIAL1.lock().write_fmt(args).expect("Printing to serial failed");
    });
}

// Expose basic IO
pub fn try_send_byte(byte: u8) -> bool {
    interrupts::without_interrupts(|| {
        let mut port = SERIAL1.lock();
        // Check LSR (Offset 5), Bit 5 = Empty Transmitter Holding Register (THRE)
        use x86_64::instructions::port::Port;
        let mut lsr: Port<u8> = Port::new(0x3F8 + 5);
        unsafe {
            if lsr.read() & 0x20 != 0 {
                port.send(byte);
                true
            } else {
                false
            }
        }
    })
}

pub fn try_read_byte() -> Option<u8> {
    interrupts::without_interrupts(|| {
        let mut port = SERIAL1.lock();
        // Check Line Status Register (Offset 5)
        // Bit 0 = Data Ready (DR)
        use x86_64::instructions::port::Port;
        let mut lsr: Port<u8> = Port::new(0x3F8 + 5);
        let mut data: Port<u8> = Port::new(0x3F8 + 0);
        
        unsafe {
            if lsr.read() & 1 == 1 {
                Some(data.read())
            } else {
                None
            }
        }
    })
}

#[macro_export]
macro_rules! serial_print {
    ($($arg:tt)*) => {
        $crate::serial::_print(format_args!($($arg)*));
    };
}

#[macro_export]
macro_rules! serial_println {
    () => ($crate::serial_print!("\n"));
    ($fmt:expr) => ($crate::serial_print!(concat!($fmt, "\n")));
    ($fmt:expr, $($arg:tt)*) => ($crate::serial_print!(concat!($fmt, "\n"), $($arg)*));
}
