import os
import base64
import subprocess

REPO_DIR = os.path.abspath(".")
CLI_PATH = os.path.join(REPO_DIR, "AetherPS4.exe")
GUI_PATH = os.path.join(REPO_DIR, "AetherPS4_GUI.exe")
README_PATH = os.path.join(REPO_DIR, "README.md")
LICENSE_PATH = os.path.join(REPO_DIR, "LICENSE")

with open(CLI_PATH, "rb") as f:
    cli_base64 = base64.b64encode(f.read()).decode("ascii")

with open(GUI_PATH, "rb") as f:
    gui_base64 = base64.b64encode(f.read()).decode("ascii")

with open(LICENSE_PATH, "r", encoding="utf-8") as f:
    license_text = f.read().replace('"', '""')

cs_source = f"""// ======================================================================
// AetherPS4 Windows Setup Installer Wizard
// Lead Architect & Developer: PRIYAN-A-1
// Copyright (c) 2026 PRIYAN-A-1. All rights reserved.
// ======================================================================

using System;
using System.IO;
using System.Drawing;
using System.Windows.Forms;
using System.Diagnostics;
using System.Text;

namespace AetherPS4Setup
{{
    public class InstallerForm : Form
    {{
        private Panel panelHeader;
        private Label lblHeaderTitle;
        private Label lblHeaderSub;
        private Panel panelContent;
        private Panel panelBottom;
        private Button btnBack;
        private Button btnNext;
        private Button btnCancel;

        // Step Panels
        private Panel pnlStep1;
        private Panel pnlStep2;
        private Panel pnlStep3;
        private Panel pnlStep4;
        private Panel pnlStep5;
        private Panel pnlStep6;

        // Step 2 Controls
        private RadioButton rbAgree;
        private RadioButton rbDisagree;

        // Step 3 Controls
        private TextBox txtInstallPath;
        private Button btnBrowse;

        // Step 4 Controls
        private CheckBox chkDesktop;
        private CheckBox chkStartMenu;

        // Step 5 Controls
        private ProgressBar progressBar;
        private Label lblProgressStatus;
        private Timer installTimer;
        private int installProgress = 0;

        // Step 6 Controls
        private CheckBox chkLaunchNow;

        private int currentStep = 1;
        private const int TOTAL_STEPS = 6;

        // Embedded payload
        private static readonly string EMBEDDED_CLI_B64 = "{cli_base64}";
        private static readonly string EMBEDDED_GUI_B64 = "{gui_base64}";
        private static readonly string EMBEDDED_LICENSE = @\"{license_text}\";

        public InstallerForm()
        {{
            InitializeComponents();
            ShowStep(1);
        }}

        private void InitializeComponents()
        {{
            this.Text = "AetherPS4 Setup - Version 1.0.0";
            this.Size = new Size(580, 440);
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.StartPosition = FormStartPosition.CenterScreen;
            this.Font = new Font("Segoe UI", 9F, FontStyle.Regular);

            // Header
            panelHeader = new Panel();
            panelHeader.Dock = DockStyle.Top;
            panelHeader.Height = 65;
            panelHeader.BackColor = Color.FromArgb(20, 24, 35);

            lblHeaderTitle = new Label();
            lblHeaderTitle.Text = "AetherPS4 Setup Wizard";
            lblHeaderTitle.Font = new Font("Segoe UI", 12F, FontStyle.Bold);
            lblHeaderTitle.ForeColor = Color.White;
            lblHeaderTitle.Location = new Point(20, 12);
            lblHeaderTitle.AutoSize = true;

            lblHeaderSub = new Label();
            lblHeaderSub.Text = "PlayStation 4 Emulator Core - Lead Architect: PRIYAN-A-1";
            lblHeaderSub.Font = new Font("Segoe UI", 9F, FontStyle.Regular);
            lblHeaderSub.ForeColor = Color.FromArgb(170, 185, 205);
            lblHeaderSub.Location = new Point(22, 38);
            lblHeaderSub.AutoSize = true;

            panelHeader.Controls.Add(lblHeaderTitle);
            panelHeader.Controls.Add(lblHeaderSub);

            // Bottom Bar
            panelBottom = new Panel();
            panelBottom.Dock = DockStyle.Bottom;
            panelBottom.Height = 50;
            panelBottom.BackColor = Color.FromArgb(240, 240, 240);

            btnCancel = new Button();
            btnCancel.Text = "Cancel";
            btnCancel.Location = new Point(480, 12);
            btnCancel.Size = new Size(75, 26);
            btnCancel.Click += (s, e) => {{ if (MessageBox.Show("Are you sure you want to cancel the installation?", "AetherPS4 Setup", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes) Application.Exit(); }};

            btnNext = new Button();
            btnNext.Text = "Next >";
            btnNext.Location = new Point(395, 12);
            btnNext.Size = new Size(75, 26);
            btnNext.Click += BtnNext_Click;

            btnBack = new Button();
            btnBack.Text = "< Back";
            btnBack.Location = new Point(310, 12);
            btnBack.Size = new Size(75, 26);
            btnBack.Click += (s, e) => {{ if (currentStep > 1) ShowStep(currentStep - 1); }};

            panelBottom.Controls.Add(btnBack);
            panelBottom.Controls.Add(btnNext);
            panelBottom.Controls.Add(btnCancel);

            // Content Area
            panelContent = new Panel();
            panelContent.Dock = DockStyle.Fill;
            panelContent.BackColor = Color.White;

            BuildStep1();
            BuildStep2();
            BuildStep3();
            BuildStep4();
            BuildStep5();
            BuildStep6();

            this.Controls.Add(panelContent);
            this.Controls.Add(panelHeader);
            this.Controls.Add(panelBottom);
        }}

        private void BuildStep1()
        {{
            pnlStep1 = new Panel {{ Dock = DockStyle.Fill }};
            Label lblWelcome = new Label();
            lblWelcome.Text = "Welcome to the AetherPS4 Setup Wizard";
            lblWelcome.Font = new Font("Segoe UI", 12F, FontStyle.Bold);
            lblWelcome.Location = new Point(30, 25);
            lblWelcome.Size = new Size(500, 30);

            Label lblDesc = new Label();
            lblDesc.Text = "This wizard will guide you through the installation of AetherPS4, a high-performance PlayStation 4 emulator core engineered by PRIYAN-A-1.\\r\\n\\r\\nFeatures:\\r\\n - Direct host x86-64 execution with System V ABI compatibility\\r\\n - Liverpool GPU PM4 Command Processor & GCN Shader Disassembly\\r\\n - 40-bit Virtual Address Space with 16KB guest page translation\\r\\n - High-Level Emulation (HLE) of Orbis OS kernel\\r\\n\\r\\nClick Next to continue, or Cancel to exit Setup.";
            lblDesc.Location = new Point(32, 65);
            lblDesc.Size = new Size(500, 180);

            pnlStep1.Controls.Add(lblWelcome);
            pnlStep1.Controls.Add(lblDesc);
            panelContent.Controls.Add(pnlStep1);
        }}

        private void BuildStep2()
        {{
            pnlStep2 = new Panel {{ Dock = DockStyle.Fill, Visible = false }};
            Label lblLicenseHdr = new Label {{ Text = "License Agreement", Font = new Font("Segoe UI", 10F, FontStyle.Bold), Location = new Point(30, 15), AutoSize = true }};
            Label lblLicenseSub = new Label {{ Text = "Please review the license terms before installing AetherPS4.", Location = new Point(30, 38), AutoSize = true }};

            TextBox txtLicense = new TextBox();
            txtLicense.Multiline = true;
            txtLicense.ReadOnly = true;
            txtLicense.ScrollBars = ScrollBars.Vertical;
            txtLicense.Location = new Point(30, 60);
            txtLicense.Size = new Size(505, 150);
            txtLicense.Text = EMBEDDED_LICENSE;

            rbAgree = new RadioButton {{ Text = "I accept the agreement", Location = new Point(32, 220), AutoSize = true }};
            rbDisagree = new RadioButton {{ Text = "I do not accept the agreement", Location = new Point(32, 245), AutoSize = true, Checked = true }};

            rbAgree.CheckedChanged += (s, e) => {{ btnNext.Enabled = rbAgree.Checked; }};

            pnlStep2.Controls.Add(lblLicenseHdr);
            pnlStep2.Controls.Add(lblLicenseSub);
            pnlStep2.Controls.Add(txtLicense);
            pnlStep2.Controls.Add(rbAgree);
            pnlStep2.Controls.Add(rbDisagree);
            panelContent.Controls.Add(pnlStep2);
        }}

        private void BuildStep3()
        {{
            pnlStep3 = new Panel {{ Dock = DockStyle.Fill, Visible = false }};
            Label lblPathHdr = new Label {{ Text = "Select Destination Location", Font = new Font("Segoe UI", 10F, FontStyle.Bold), Location = new Point(30, 20), AutoSize = true }};
            Label lblPathSub = new Label {{ Text = "Setup will install AetherPS4 into the following folder.", Location = new Point(30, 45), AutoSize = true }};

            string defaultPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs\\\\AetherPS4");
            txtInstallPath = new TextBox {{ Text = defaultPath, Location = new Point(30, 85), Size = new Size(415, 24) }};
            btnBrowse = new Button {{ Text = "Browse...", Location = new Point(455, 84), Size = new Size(80, 26) }};
            btnBrowse.Click += (s, e) => {{
                FolderBrowserDialog fbd = new FolderBrowserDialog {{ SelectedPath = txtInstallPath.Text }};
                if (fbd.ShowDialog() == DialogResult.OK) txtInstallPath.Text = fbd.SelectedPath;
            }};

            pnlStep3.Controls.Add(lblPathHdr);
            pnlStep3.Controls.Add(lblPathSub);
            pnlStep3.Controls.Add(txtInstallPath);
            pnlStep3.Controls.Add(btnBrowse);
            panelContent.Controls.Add(pnlStep3);
        }}

        private void BuildStep4()
        {{
            pnlStep4 = new Panel {{ Dock = DockStyle.Fill, Visible = false }};
            Label lblTaskHdr = new Label {{ Text = "Select Additional Tasks", Font = new Font("Segoe UI", 10F, FontStyle.Bold), Location = new Point(30, 20), AutoSize = true }};
            Label lblTaskSub = new Label {{ Text = "Which additional shortcuts should be created?", Location = new Point(30, 45), AutoSize = true }};

            chkDesktop = new CheckBox {{ Text = "Create a Desktop shortcut", Location = new Point(32, 85), AutoSize = true, Checked = true }};
            chkStartMenu = new CheckBox {{ Text = "Create a Start Menu shortcut", Location = new Point(32, 115), AutoSize = true, Checked = true }};

            pnlStep4.Controls.Add(lblTaskHdr);
            pnlStep4.Controls.Add(lblTaskSub);
            pnlStep4.Controls.Add(chkDesktop);
            pnlStep4.Controls.Add(chkStartMenu);
            panelContent.Controls.Add(pnlStep4);
        }}

        private void BuildStep5()
        {{
            pnlStep5 = new Panel {{ Dock = DockStyle.Fill, Visible = false }};
            Label lblInstHdr = new Label {{ Text = "Installing AetherPS4", Font = new Font("Segoe UI", 10F, FontStyle.Bold), Location = new Point(30, 25), AutoSize = true }};
            lblProgressStatus = new Label {{ Text = "Extracting files...", Location = new Point(30, 55), AutoSize = true }};

            progressBar = new ProgressBar {{ Location = new Point(30, 85), Size = new Size(505, 25), Minimum = 0, Maximum = 100 }};

            installTimer = new Timer {{ Interval = 40 }};
            installTimer.Tick += InstallTimer_Tick;

            pnlStep5.Controls.Add(lblInstHdr);
            pnlStep5.Controls.Add(lblProgressStatus);
            pnlStep5.Controls.Add(progressBar);
            panelContent.Controls.Add(pnlStep5);
        }}

        private void BuildStep6()
        {{
            pnlStep6 = new Panel {{ Dock = DockStyle.Fill, Visible = false }};
            Label lblDoneHdr = new Label {{ Text = "Completing the AetherPS4 Setup Wizard", Font = new Font("Segoe UI", 12F, FontStyle.Bold), Location = new Point(30, 30), Size = new Size(500, 30) }};
            Label lblDoneDesc = new Label {{ Text = "AetherPS4 has been successfully installed on your computer.\\r\\n\\r\\nClick Finish to exit Setup.", Location = new Point(32, 75), Size = new Size(500, 60) }};

            chkLaunchNow = new CheckBox {{ Text = "Launch AetherPS4 now", Location = new Point(32, 140), AutoSize = true, Checked = true }};

            pnlStep6.Controls.Add(lblDoneHdr);
            pnlStep6.Controls.Add(lblDoneDesc);
            pnlStep6.Controls.Add(chkLaunchNow);
            panelContent.Controls.Add(pnlStep6);
        }}

        private void ShowStep(int step)
        {{
            currentStep = step;
            pnlStep1.Visible = (step == 1);
            pnlStep2.Visible = (step == 2);
            pnlStep3.Visible = (step == 3);
            pnlStep4.Visible = (step == 4);
            pnlStep5.Visible = (step == 5);
            pnlStep6.Visible = (step == 6);

            btnBack.Enabled = (step > 1 && step < 5);
            btnCancel.Enabled = (step < 5);

            if (step == 2)
            {{
                btnNext.Enabled = rbAgree.Checked;
            }}
            else if (step == 4)
            {{
                btnNext.Text = "Install";
            }}
            else if (step == 5)
            {{
                btnNext.Enabled = false;
                btnBack.Enabled = false;
                btnNext.Text = "Next >";
                StartInstallation();
            }}
            else if (step == 6)
            {{
                btnNext.Enabled = true;
                btnNext.Text = "Finish";
                btnCancel.Enabled = false;
                btnBack.Enabled = false;
            }}
            else
            {{
                btnNext.Enabled = true;
                btnNext.Text = "Next >";
            }}
        }}

        private void BtnNext_Click(object sender, EventArgs e)
        {{
            if (currentStep == TOTAL_STEPS)
            {{
                if (chkLaunchNow.Checked)
                {{
                    string exePath = Path.Combine(txtInstallPath.Text, "AetherPS4_GUI.exe");
                    if (!File.Exists(exePath)) exePath = Path.Combine(txtInstallPath.Text, "AetherPS4.exe");
                    if (File.Exists(exePath))
                    {{
                        Process.Start(new ProcessStartInfo {{ FileName = exePath, UseShellExecute = true }});
                    }}
                }}
                Application.Exit();
            }}
            else if (currentStep < TOTAL_STEPS)
            {{
                ShowStep(currentStep + 1);
            }}
        }}

        private void StartInstallation()
        {{
            installProgress = 0;
            progressBar.Value = 0;
            installTimer.Start();
        }}

        private void InstallTimer_Tick(object sender, EventArgs e)
        {{
            installProgress += 4;
            if (installProgress <= 100)
            {{
                progressBar.Value = installProgress;
                if (installProgress == 20) lblProgressStatus.Text = "Creating target directories...";
                else if (installProgress == 40) lblProgressStatus.Text = "Extracting AetherPS4 emulator core...";
                else if (installProgress == 70) lblProgressStatus.Text = "Writing shortcuts and uninstaller...";
                else if (installProgress == 90) lblProgressStatus.Text = "Finalizing configuration...";
            }}
            else
            {{
                installTimer.Stop();
                PerformActualInstall();
                ShowStep(6);
            }}
        }}

        private void PerformActualInstall()
        {{
            try
            {{
                string targetDir = txtInstallPath.Text;
                if (!Directory.Exists(targetDir))
                {{
                    Directory.CreateDirectory(targetDir);
                }}

                // 1. Write AetherPS4.exe (CLI) and AetherPS4_GUI.exe (Desktop GUI)
                string cliTarget = Path.Combine(targetDir, "AetherPS4.exe");
                byte[] cliBytes = Convert.FromBase64String(EMBEDDED_CLI_B64);
                File.WriteAllBytes(cliTarget, cliBytes);

                string guiTarget = Path.Combine(targetDir, "AetherPS4_GUI.exe");
                byte[] guiBytes = Convert.FromBase64String(EMBEDDED_GUI_B64);
                File.WriteAllBytes(guiTarget, guiBytes);

                // 2. Write Uninstaller batch
                string uninstallerPath = Path.Combine(targetDir, "Uninstall.bat");
                string uninstScript = "@echo off\\r\\ntitle Uninstall AetherPS4\\r\\necho Uninstalling AetherPS4...\\r\\ntimeout /t 2 /nobreak >nul\\r\\ncd ..\\r\\nrmdir /s /q \\\"" + targetDir + "\\\"\\r\\necho AetherPS4 successfully uninstalled.\\r\\npause";
                File.WriteAllText(uninstallerPath, uninstScript);

                // 3. Shortcuts to GUI
                if (chkDesktop.Checked)
                {{
                    CreateShortcut(Environment.GetFolderPath(Environment.SpecialFolder.Desktop), "AetherPS4.lnk", guiTarget);
                }}

                if (chkStartMenu.Checked)
                {{
                    string startMenuProg = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), "AetherPS4");
                    if (!Directory.Exists(startMenuProg)) Directory.CreateDirectory(startMenuProg);
                    CreateShortcut(startMenuProg, "AetherPS4.lnk", guiTarget);
                }}
            }}
            catch (Exception ex)
            {{
                MessageBox.Show("Installation note: " + ex.Message, "Setup", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }}
        }}

        private void CreateShortcut(string folder, string shortcutName, string targetPath)
        {{
            try
            {{
                Type shellType = Type.GetTypeFromProgID("WScript.Shell");
                if (shellType != null)
                {{
                    dynamic shell = Activator.CreateInstance(shellType);
                    dynamic shortcut = shell.CreateShortcut(Path.Combine(folder, shortcutName));
                    shortcut.TargetPath = targetPath;
                    shortcut.WorkingDirectory = Path.GetDirectoryName(targetPath);
                    shortcut.Description = "AetherPS4 - PlayStation 4 Emulator Core by PRIYAN-A-1";
                    shortcut.Save();
                }}
            }}
            catch {{ }}
        }}

        [STAThread]
        public static void Main()
        {{
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new InstallerForm());
        }}
    }}
}}
"""

cs_file = os.path.join(REPO_DIR, "AetherPS4_Installer.cs")
with open(cs_file, "w", encoding="utf-8") as f:
    f.write(cs_source)

print("Generated AetherPS4_Installer.cs successfully.")
