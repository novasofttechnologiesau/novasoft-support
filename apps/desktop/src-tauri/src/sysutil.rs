//! Runs a small, fixed set of OS commands needed for diagnostics/repair actions.
//!
//! SECURITY BOUNDARY: every call site in this codebase passes a hardcoded program name and
//! hardcoded argument list -- never a string built from user input, ticket text, or an AI
//! response. There is no code path anywhere that lets a caller supply an arbitrary command or
//! argument. If you're adding a new call, keep it that way: hardcode the program and args at
//! the call site, don't accept them as parameters from outside this process.

use std::process::Command;

pub fn run_fixed_command(program: &str, args: &[&str]) -> Result<String, String> {
    let output = Command::new(program)
        .args(args)
        .output()
        .map_err(|e| format!("Failed to run {program}: {e}"))?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        return Err(format!("{program} exited with {}: {stderr}", output.status));
    }
    Ok(stdout)
}
