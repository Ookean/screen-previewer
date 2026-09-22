; installer.iss
; Inno Setup script for Screen Preview Tool
; Download Inno Setup (for local testing) from https://jrsoftware.org/isdl.php
; In CI this is compiled headlessly by the ISCC.exe compiler - see the workflow file.

#define MyAppName "Screen Preview"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "OokeanDevelopments"
#define MyAppExeName "screen_preview.exe"

[Setup]
AppId={{B6A2B1D4-7B0E-4C4E-9F0A-6D1C8E9F2A11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
; NOTE: the "Select Destination Location" page (where the user can browse to
; a different install path) is shown by default - it only disappears if you
; set DisableDirPage=yes, which we deliberately do NOT do here.
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=ScreenPreview-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; UninstallDisplayIcon lets it show up nicely in "Add or Remove Programs"
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
AppVerName={#MyAppName} {#MyAppVersion}
; Requires 64-bit Windows (matches the PyInstaller build produced on windows-latest runners)
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
; Windows 10 or newer
MinVersion=10.0
; Lets the user pick "install for me only" (no admin, installs under AppData -
; no UAC prompt) vs "install for all users" (needs admin, goes to Program Files).
; This also matters for SmartScreen: an unsigned installer that doesn't demand
; admin rights is a slightly smaller ask for a cautious user.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; This expects the PyInstaller build to already be in dist\screen_preview.exe
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName} now"; Flags: nowait postinstall skipifsilent
