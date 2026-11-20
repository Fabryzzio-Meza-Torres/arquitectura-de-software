import os, subprocess, sys, glob

os.chdir("/kaggle/working")
print("=== runner: installing deps ===", flush=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                "sentence-transformers==6.3.0", "bm25s==0.3.16", "PyStemmer==3.1.0", "faiss-cpu"],
               check=True)
alpha = glob.glob("/kaggle/input/**/alpha.json", recursive=True)
script = glob.glob("/kaggle/input/**/minion_bench.py", recursive=True)
os.system("ls -R /kaggle/input | head -30")
print("alpha:", alpha, "script:", script, flush=True)
subprocess.run([sys.executable, "-u", script[0], "--dataset", "fiqa", "--pilot",
                "--reps", "1", "--alpha", alpha[0], "--data-dir", "data",
                "--out", "results", "--encode-batch", "128"], check=True)
subprocess.run(["tar", "-czf", "results.tar.gz", "results"], check=True)
print("=== runner done ===", flush=True)
