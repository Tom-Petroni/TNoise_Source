unsafe extern "C" {
    fn tnoise_base_keepalive();
}

#[unsafe(no_mangle)]
pub extern "C" fn tnoise_base_rust_link() {
    unsafe {
        tnoise_base_keepalive();
    }
}
