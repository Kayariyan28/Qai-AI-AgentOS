use conquer_once::spin::OnceCell;
use crossbeam_queue::ArrayQueue;
use core::{pin::Pin, task::{Context, Poll}};
use futures_util::stream::Stream;
use futures_util::task::AtomicWaker;

static SCANCODE_QUEUE: OnceCell<ArrayQueue<u8>> = OnceCell::uninit();
static WAKER: AtomicWaker = AtomicWaker::new();

/// Called by the keyboard interrupt handler
/// Must not block or allocate.
pub(crate) fn add_scancode(scancode: u8) {
    if let Ok(queue) = SCANCODE_QUEUE.try_get() {
        if let Err(_) = queue.push(scancode) {
            // crate::serial_println!("WARNING: scancode queue full; dropping input");
        } else {
            // crate::serial_println!("WAKE: {}", scancode); // DEBUG
            WAKER.wake();
        }
    } else {
        // crate::serial_println!("WARNING: scancode queue uninitialized");
    }
}

pub struct ScancodeStream {
    _private: (),
}

impl ScancodeStream {
    pub fn new() -> Self {
        SCANCODE_QUEUE.try_init_once(|| ArrayQueue::new(100))
            .expect("ScancodeStream::new should only be called once");
        ScancodeStream { _private: () }
    }
}

impl Stream for ScancodeStream {
    type Item = u8;

    fn poll_next(self: Pin<&mut Self>, cx: &mut Context) -> Poll<Option<u8>> {
        let queue = SCANCODE_QUEUE
            .try_get()
            .expect("scancode queue not initialized");

        // 1. Fast path: Check queue (populated by interrupt)
        if let Some(scancode) = queue.pop() {
            return Poll::Ready(Some(scancode));
        }

        // 2. Hybrid Polling path: Check hardware directly
        // This acts as a fallback if interrupts are masked or failing.
        // We rely on the Timer interrupt to wake the executor loop frequently enough.
        // 2. Hybrid Polling path: DISABLED
        // We rely solely on the interrupt handler now.
        // If interrupts are broken, we want to know, rather than hiding it with polling.
        
        /*
        use x86_64::instructions::port::Port;
        let mut status_port = Port::<u8>::new(0x64);
        let mut data_port = Port::<u8>::new(0x60);

        unsafe {
            let status = status_port.read();
            if status & 1 != 0 { // Output Buffer Full (Bit 0)
                let scancode = data_port.read();
                return Poll::Ready(Some(scancode));
            }
        }
        */

        WAKER.register(&cx.waker());
        
        // Double check queue in case interrupt fired during registration
        match queue.pop() {
            Some(scancode) => {
                WAKER.take();
                Poll::Ready(Some(scancode))
            }
            None => {
                // Trust the interrupt handler to wake us
                // Don't busy poll - it causes race conditions
                Poll::Pending
            }
        }
    }
}
