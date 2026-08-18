using AxWMPLib;
using Python.Runtime;
using System.Text.Json;
using System.Windows.Forms;
using System.IO;
namespace chat
{

    public partial class Form1 : Form
    {

        public Form1()
        {
            InitializeComponent();
            lastSize = this.ClientSize;
            this.Resize += (s, e) =>
            {
                this.Scale(new SizeF((float)this.ClientSize.Width / lastSize.Width,
                                      (float)this.ClientSize.Height / lastSize.Height));
                lastSize = this.ClientSize;
            };
        }

        private Size lastSize;

        private void label1_Click(object sender, EventArgs e)
        {

        }

        private void run_python(string scriptName)
        {


        }
        private void AppendColoredText(RichTextBox box, string text, Color color)
        {
            box.SelectionStart = box.TextLength;
            box.SelectionLength = 0;
            box.SelectionColor = color;
            box.AppendText(text);
            box.SelectionColor = box.ForeColor;
        }




        private async void send_btn_Click(object sender, EventArgs e)
        {
            string userQuery = input_txt.Text;
            if (string.IsNullOrWhiteSpace(userQuery)) return;

            AppendColoredText(chat, "أنت: ", Color.Cyan);
            AppendColoredText(chat, userQuery + Environment.NewLine, Color.Cyan);

            input_txt.Clear();
            send_btn.Enabled = false;
            sound_player.URL = null;
            if (!PythonEngine.IsInitialized)
            {
                Runtime.PythonDLL = @"python312.dll";
                PythonEngine.Initialize();
                PythonEngine.BeginAllowThreads();
            }

            string rawJson = await Task.Run(() =>
            {
                try
                {
                    using (Py.GIL())
                    {
                        dynamic sys = Py.Import("sys");
                        sys.path.append(@".venv\Lib\site-packages");
                        sys.path.append(@"Agent2");
                        if (Agent.Checked)
                        {
                            dynamic asyncioModule = Py.Import("asyncio");
                            asyncioModule.set_event_loop_policy(asyncioModule.WindowsSelectorEventLoopPolicy());
                            dynamic pyscript = Py.Import("app");
                            dynamic rawResult = asyncioModule.run(pyscript.run_ai(userQuery));
                            return rawResult?.ToString() ?? "{}";
                        }
                        else if (RAG.Checked)
                        {
                            sys.path.append(@"chatpopa\RAG");
                            dynamic fn = Py.Import("chat1");
                            dynamic rawResult = fn.llm_sent(userQuery);
                            return rawResult?.ToString() ?? "{}";
                        }
                        return "error!!!!!!!";
                    }
                }
                catch (Exception ex)
                {
                    return JsonSerializer.Serialize(new { text = $"خطأ: {ex.Message}", media = new object[0] });
                }
            });

            // فك الـ JSON
            using JsonDocument doc = JsonDocument.Parse(rawJson);
            var root = doc.RootElement;
            string text = root.GetProperty("text").GetString() ?? "";

            AppendColoredText(chat, "الوكيل: ", Color.Orange);
            AppendColoredText(chat, text + Environment.NewLine, Color.Yellow);

            if (root.TryGetProperty("media", out JsonElement mediaArray))
            {
                foreach (var item in mediaArray.EnumerateArray())
                {


                    string type = item.TryGetProperty("type", out var t) ? t.GetString()
                            : item.TryGetProperty("img", out var i) ? "image"
                            : "";

                    string Data = item.TryGetProperty("data", out var d) ? d.GetString()
                                 : item.TryGetProperty("url", out var u) ? u.GetString()
                                 : "";

                    if (type == "image" || type == "img")
                    {
                        img.SizeMode = PictureBoxSizeMode.Zoom;

                        string img_url = Data;
                        if (File.Exists(img_url))
                        {
                            img.Image = new Bitmap(img_url);
                        }
                        else chat.AppendText("لا توجد صورة " + img_url + Environment.NewLine);
                    }
                    else if (type == "audio")
                    {
                        string audioPath = Data;
                        if (File.Exists(audioPath))
                        {
                            sound_player.settings.autoStart = false;
                            sound_player.URL = audioPath;

                        }
                        else
                        {
                            chat.AppendText("تعذر إيجاد ملف الصوت: " + audioPath + Environment.NewLine);
                        }
                    }

                }
            }

            send_btn.Enabled = true;
        }
        private void button1_Click(object sender, EventArgs e)
        {
            if (PythonEngine.IsInitialized)
            {
                PythonEngine.Shutdown();
            }
            this.Close();
        }

        private void RAG_CheckedChanged(object sender, EventArgs e)
        {

        }

        private void button2_Click(object sender, EventArgs e)
        {
            chat.Text= string.Empty;
            img.Image= null;
            sound_player.URL= null;
        }
    }
}
    

