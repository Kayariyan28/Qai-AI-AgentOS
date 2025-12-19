use alloc::collections::BTreeMap;
use alloc::string::String;
use alloc::vec::Vec;
use spin::Mutex;
use lazy_static::lazy_static;

pub struct MemFS {
    files: BTreeMap<String, Vec<u8>>,
}

impl MemFS {
    pub fn new() -> Self {
        Self {
            files: BTreeMap::new(),
        }
    }
}

lazy_static! {
    pub static ref FILESYSTEM: Mutex<MemFS> = Mutex::new(MemFS::new());
}

pub fn init() {
    // Force lazy initialization
    let _ = FILESYSTEM.lock();
    crate::serial_println!("MemFS: Initialized");
}

pub fn write_file(path: &str, content: &[u8]) {
    let mut fs = FILESYSTEM.lock();
    fs.files.insert(String::from(path), Vec::from(content));
}

pub fn read_file(path: &str) -> Option<Vec<u8>> {
    let fs = FILESYSTEM.lock();
    fs.files.get(path).cloned()
}

pub fn list_dir() -> Vec<String> {
    let fs = FILESYSTEM.lock();
    fs.files.keys().cloned().collect()
}
