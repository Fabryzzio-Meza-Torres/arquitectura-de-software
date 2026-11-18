import glob, os, shutil, subprocess, sys, tarfile

os.chdir("/kaggle/working")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "sentence-transformers==6.3.0", "bm25s==0.3.16",
                "PyStemmer==3.1.0", "faiss-cpu"], check=True)
alpha = glob.glob("/kaggle/input/**/alpha.json", recursive=True)[0]
script = glob.glob("/kaggle/input/**/minion_bench.py", recursive=True)[0]
cal_tar = glob.glob("/kaggle/input/**/calibration_fiqa.tar.gz", recursive=True)
if cal_tar:
    with tarfile.open(cal_tar[0]) as t:
        t.extractall(".")
else:  # Kaggle auto-extracts archives uploaded to datasets
    src = glob.glob("/kaggle/input/**/calibration_fiqa/results", recursive=True)[0]
    shutil.copytree(src, "results", dirs_exist_ok=True)
shutil.move("results/fiqa/run_meta.json", "results/fiqa/run_meta_calibration.json")
try:
    subprocess.run([sys.executable, "-u", script, "--dataset", "fiqa", "--alpha", alpha, "--data-dir", "/tmp/data",
                    "--out", "results", "--encode-batch", "128", "--reps", "3",
                    "--calibration", "results/fiqa/calibration.json"], check=True)
finally:
    subprocess.run(["tar", "-czf", "results.tar.gz", "results"])
