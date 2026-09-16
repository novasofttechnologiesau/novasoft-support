mod commands;
mod sysutil;
mod types;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            commands::diagnostics::get_device_health,
            commands::diagnostics::get_network_diagnostics,
            commands::diagnostics::get_printer_diagnostics,
            commands::diagnostics::get_onedrive_diagnostics,
            commands::diagnostics::get_outlook_diagnostics,
        ])
        .run(tauri::generate_context!())
        .expect("error while running NovaSoft Support");
}
