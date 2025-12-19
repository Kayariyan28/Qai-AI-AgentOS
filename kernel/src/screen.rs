use core::fmt;
use bootloader_api::info::{FrameBufferInfo, PixelFormat};
use font8x8::UnicodeFonts;
use spin::Mutex;
use lazy_static::lazy_static;
use alloc::vec::Vec;
use alloc::string::String;

/// Max lines to keep in scroll buffer
const SCROLL_BUFFER_SIZE: usize = 200;

pub struct FrameBufferWriter {
    buffer: &'static mut [u8],
    info: FrameBufferInfo,
    x_pos: usize,
    y_pos: usize,
    scale: usize,
    color: [u8; 3],
    // Scroll buffer
    lines: Vec<String>,
    current_line: String,
    scroll_offset: usize,  // 0 = viewing most recent
    lines_on_screen: usize,
}

impl FrameBufferWriter {
    pub fn new(buffer: &'static mut [u8], info: FrameBufferInfo) -> Self {
        let font_height = 8 + 4; // 8px font + 4px padding
        let lines_on_screen = info.height / font_height;
        
        let mut writer = Self {
            buffer,
            info,
            x_pos: 0,
            y_pos: 0,
            scale: 1,
            color: [255, 255, 255],
            lines: Vec::new(),
            current_line: String::new(),
            scroll_offset: 0,
            lines_on_screen,
        };
        writer.clear();
        writer
    }

    pub fn set_color(&mut self, r: u8, g: u8, b: u8) {
        self.color = [r, g, b];
    }

    pub fn set_scale(&mut self, scale: usize) {
        self.scale = scale;
    }

    pub fn set_cursor(&mut self, x: usize, y: usize) {
        self.x_pos = x;
        self.y_pos = y;
    }

    pub fn width(&self) -> usize {
        self.info.width
    }
    
    pub fn height(&self) -> usize {
        self.info.height
    }

    pub fn clear(&mut self) {
        self.x_pos = 0;
        self.y_pos = 0;
        self.buffer.fill(0);
    }

    /// Scroll up (view older content)
    pub fn scroll_up(&mut self) {
        let max_scroll = self.lines.len().saturating_sub(self.lines_on_screen);
        if self.scroll_offset < max_scroll {
            self.scroll_offset += 3;
            if self.scroll_offset > max_scroll {
                self.scroll_offset = max_scroll;
            }
            self.redraw();
        }
    }

    /// Scroll down (view newer content)
    pub fn scroll_down(&mut self) {
        if self.scroll_offset > 0 {
            if self.scroll_offset >= 3 {
                self.scroll_offset -= 3;
            } else {
                self.scroll_offset = 0;
            }
            self.redraw();
        }
    }

    /// Redraw screen from scroll buffer
    fn redraw(&mut self) {
        self.buffer.fill(0);
        self.x_pos = 0;
        self.y_pos = 0;
        
        let total_lines = self.lines.len();
        let start_idx = total_lines.saturating_sub(self.lines_on_screen + self.scroll_offset);
        let end_idx = total_lines.saturating_sub(self.scroll_offset);
        
        // Clone lines to avoid borrow conflict
        let lines_to_draw: Vec<String> = (start_idx..end_idx)
            .filter(|&idx| idx < self.lines.len())
            .map(|idx| self.lines[idx].clone())
            .collect();
        
        for line in lines_to_draw {
            for c in line.chars() {
                if c != '\n' {
                    self.draw_char(c);
                }
            }
            self.newline_draw();
        }
        
        // Show scroll indicator if not at bottom
        if self.scroll_offset > 0 {
            let old_color = self.color;
            self.color = [255, 255, 0]; // Yellow
            let indicator = "[SCROLL MODE - PgDn to return]";
            let save_x = self.x_pos;
            let save_y = self.y_pos;
            self.x_pos = 0;
            self.y_pos = self.info.height - 16;
            for c in indicator.chars() {
                self.draw_char(c);
            }
            self.x_pos = save_x;
            self.y_pos = save_y;
            self.color = old_color;
        }
    }

    pub fn draw_line(&mut self, x0: usize, y0: usize, x1: usize, y1: usize) {
        let mut x = x0 as isize;
        let mut y = y0 as isize;
        let dx = (x1 as isize - x0 as isize).abs();
        let dy = -(y1 as isize - y0 as isize).abs();
        let sx = if x0 < x1 { 1 } else { -1 };
        let sy = if y0 < y1 { 1 } else { -1 };
        let mut err = dx + dy;

        loop {
            if x >= 0 && x < self.width() as isize && y >= 0 && y < self.height() as isize {
                 self.write_pixel(x as usize, y as usize, self.color[0], self.color[1], self.color[2]);
            }

            if x == x1 as isize && y == y1 as isize { break; }
            let e2 = 2 * err;
            if e2 >= dy {
                err += dy;
                x += sx;
            }
            if e2 <= dx {
                err += dx;
                y += sy;
            }
        }
    }

    pub fn draw_rect(&mut self, x: usize, y: usize, w: usize, h: usize) {
        self.draw_line(x, y, x + w, y);
        self.draw_line(x + w, y, x + w, y + h);
        self.draw_line(x + w, y + h, x, y + h);
        self.draw_line(x, y + h, x, y);
    }

    pub fn fill_rect(&mut self, x: usize, y: usize, w: usize, h: usize) {
        for i in 0..h {
            self.draw_line(x, y + i, x + w, y + i);
        }
    }
    
    pub fn draw_circle(&mut self, xc: usize, yc: usize, r: usize) {
        let mut x = 0;
        let mut y = r as isize;
        let mut d = 3 - 2 * r as isize;

        self.draw_circle_octants(xc, yc, x, y as usize);

        while y >= x as isize {
            x += 1;
            if d > 0 {
                y -= 1;
                d = d + 4 * (x as isize - y) + 10;
            } else {
                d = d + 4 * x as isize + 6;
            }
            self.draw_circle_octants(xc, yc, x, y as usize);
        }
    }

    fn draw_circle_octants(&mut self, xc: usize, yc: usize, x: usize, y: usize) {
        let points = [
            (xc + x, yc + y), (xc - x, yc + y), (xc + x, yc - y), (xc - x, yc - y),
            (xc + y, yc + x), (xc - y, yc + x), (xc + y, yc - x), (xc - y, yc - x)
        ];
        
        for (px, py) in points.iter() {
            if *px < self.width() && *py < self.height() {
                self.write_pixel(*px, *py, self.color[0], self.color[1], self.color[2]);
            }
        }
    }

    fn write_pixel(&mut self, x: usize, y: usize, r: u8, g: u8, b: u8) {
        let pixel_offset = y * self.info.stride + x;
        let byte_offset = pixel_offset * self.info.bytes_per_pixel;
        
        if byte_offset >= self.buffer.len() {
             return;
        }

        let pixel_buffer = &mut self.buffer[byte_offset..];
        match self.info.pixel_format {
            PixelFormat::Rgb => {
                pixel_buffer[0] = r;
                pixel_buffer[1] = g;
                pixel_buffer[2] = b;
            }
            PixelFormat::Bgr => {
                pixel_buffer[0] = b;
                pixel_buffer[1] = g;
                pixel_buffer[2] = r;
            }
            PixelFormat::U8 => {
                 if let Some(p) = pixel_buffer.get_mut(0) {
                     *p = g;
                 }
            }
            _ => {}
        }
    }

    fn draw_char(&mut self, c: char) {
        let font_size = 8 * self.scale;
        
        if self.x_pos + font_size >= self.info.width {
            self.newline_draw();
        }
        
        if self.y_pos + font_size >= self.info.height {
            return; // Don't draw off screen
        }

        let rendered = font8x8::BASIC_FONTS.get(c)
            .unwrap_or(font8x8::BASIC_FONTS.get('?').unwrap());

        for (y, byte) in rendered.iter().enumerate() {
            for x in 0..8 {
                if (byte >> x) & 1 == 1 {
                     for dy in 0..self.scale {
                         for dx in 0..self.scale {
                             self.write_pixel(
                                 self.x_pos + (x * self.scale) + dx, 
                                 self.y_pos + (y * self.scale) + dy, 
                                 self.color[0], self.color[1], self.color[2]
                             );
                         }
                     }
                }
            }
        }
        self.x_pos += font_size;
    }

    fn newline_draw(&mut self) {
        self.y_pos += 8 * self.scale + 4;
        self.x_pos = 0;
    }

    fn write_char(&mut self, c: char) {
        match c {
            '\n' => {
                self.lines.push(self.current_line.clone());
                self.current_line.clear();
                
                // Trim buffer if too large
                while self.lines.len() > SCROLL_BUFFER_SIZE {
                    self.lines.remove(0);
                }
                
                // Only redraw if not scrolled
                if self.scroll_offset == 0 {
                    self.newline_draw();
                    // Check if we need to scroll the display
                    let font_height = 8 * self.scale + 4;
                    if self.y_pos + font_height >= self.info.height {
                        self.redraw();
                    }
                }
            }
            _ => {
                self.current_line.push(c);
                
                if self.scroll_offset == 0 {
                    let font_size = 8 * self.scale;
                    if self.x_pos + font_size >= self.info.width {
                        self.newline_draw();
                    }
                    if self.y_pos + font_size < self.info.height {
                        self.draw_char(c);
                    }
                }
            }
        }
    }
}

pub static WRITER: Mutex<Option<FrameBufferWriter>> = Mutex::new(None);

pub fn init(buffer: &'static mut [u8], info: FrameBufferInfo) {
    let writer = FrameBufferWriter::new(buffer, info);
    *WRITER.lock() = Some(writer);
}

pub fn scroll_up() {
    use x86_64::instructions::interrupts;
    interrupts::without_interrupts(|| {
        if let Some(writer) = WRITER.lock().as_mut() {
            writer.scroll_up();
        }
    });
}

pub fn scroll_down() {
    use x86_64::instructions::interrupts;
    interrupts::without_interrupts(|| {
        if let Some(writer) = WRITER.lock().as_mut() {
            writer.scroll_down();
        }
    });
}

// Public Graphics API
pub fn draw_line(x0: usize, y0: usize, x1: usize, y1: usize) {
    use x86_64::instructions::interrupts;
    interrupts::without_interrupts(|| {
        if let Some(writer) = WRITER.lock().as_mut() {
            writer.draw_line(x0, y0, x1, y1);
        }
    });
}

pub fn clear_screen() {
    use x86_64::instructions::interrupts;
    interrupts::without_interrupts(|| {
        if let Some(writer) = WRITER.lock().as_mut() {
            writer.clear();
        }
    });
}

pub fn set_color(r: u8, g: u8, b: u8) {
    use x86_64::instructions::interrupts;
    interrupts::without_interrupts(|| {
        if let Some(writer) = WRITER.lock().as_mut() {
            writer.set_color(r, g, b);
        }
    });
}

pub fn redraw() {
    use x86_64::instructions::interrupts;
    interrupts::without_interrupts(|| {
        if let Some(writer) = WRITER.lock().as_mut() {
            writer.redraw();
        }
    });
}

pub fn fill_rect(x: usize, y: usize, w: usize, h: usize) {
    use x86_64::instructions::interrupts;
    interrupts::without_interrupts(|| {
        if let Some(writer) = WRITER.lock().as_mut() {
            writer.fill_rect(x, y, w, h);
        }
    });
}

pub fn set_cursor(x: usize, y: usize) {
    use x86_64::instructions::interrupts;
    interrupts::without_interrupts(|| {
        if let Some(writer) = WRITER.lock().as_mut() {
            writer.set_cursor(x, y);
        }
    });
}

#[doc(hidden)]
pub fn _print(args: fmt::Arguments) {
    use core::fmt::Write;
    use x86_64::instructions::interrupts;

    interrupts::without_interrupts(|| {
        if let Some(writer) = WRITER.lock().as_mut() {
            writer.write_fmt(args).unwrap();
        }
    });
}

#[macro_export]
macro_rules! print {
    ($($arg:tt)*) => ($crate::screen::_print(format_args!($($arg)*)));
}

#[macro_export]
macro_rules! println {
    () => ($crate::print!("\n"));
    ($($arg:tt)*) => ($crate::print!("{}\n", format_args!($($arg)*)));
}

impl fmt::Write for FrameBufferWriter {
    fn write_str(&mut self, s: &str) -> fmt::Result {
        for c in s.chars() {
            self.write_char(c);
        }
        Ok(())
    }
}
