import os, subprocess, sys, glob

os.chdir("/kaggle/working")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "sentence-transformers==6.3.0", "bm25s==0.3.16",
                "PyStemmer==3.1.0", "faiss-cpu"], check=True)
alpha = glob.glob("/kaggle/input/**/alpha.json", recursive=True)[0]
script = glob.glob("/kaggle/input/**/minion_bench.py", recursive=True)[0]
try:
    subprocess.run([sys.executable, "-u", script, "--dataset", "fiqa", "--phase", "calibrate", "--alpha", alpha,
                    "--data-dir", "data", "--out", "results", "--encode-batch", "128"], check=True)
finally:
    subprocess.run(["tar", "-czf", "results.tar.gz", "results"])
