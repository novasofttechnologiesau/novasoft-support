use serde::Serialize;

#[derive(Serialize)]
#[serde(rename_all = "snake_case")]
pub struct DiagnosticReport<T: Serialize> {
    pub diagnostic_pack: &'static str,
    pub device_name: String,
    pub timestamp: String,
    pub results: T,
    pub severity: &'static str,
}

#[derive(Serialize)]
#[serde(rename_all = "snake_case")]
pub struct ActionResult {
    pub action: &'static str,
    pub success: bool,
    pub message: String,
    pub timestamp: String,
}

pub fn now_iso() -> String {
    chrono::Local::now().to_rfc3339()
}

pub fn device_name() -> String {
    sysinfo::System::host_name().unwrap_or_else(|| "UNKNOWN-DEVICE".to_string())
}
