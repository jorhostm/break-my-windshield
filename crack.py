import numpy as np
import pandas as pd
import glob
import seaborn as sns
import matplotlib.pyplot as plt

csvs = dict()
df_dict = dict()

for folder in ["NEW", "SUV", "CC1"]:
    for filename in glob.iglob(f"{folder}/{folder}*.csv"):
        _df = pd.read_csv(filename)
        df_dict[filename.removeprefix(f"{folder}\\")] = _df
    

def avg_speed(df):
    frame = df.Frame.to_numpy()
    x = df.X.to_numpy()
    y = df.Y.to_numpy()
    dist = np.sum(np.hypot(x[1:]-x[:-1], y[1:]-y[:-1]))
    time = (frame[-1] - frame[0])/25000
    
    if time <= 0:
        return 0
    else:
        return dist/time/1000


data = []
for filename,df in df_dict.items():
    split = filename.removesuffix(".csv").split("_")
    data.append((avg_speed(df), split[0],split[1],split[2],split[3],split[4],split[5]))

speeds = pd.DataFrame(data, columns=["avg_speed","ws_type","ws_num","crack_num","camera","crack_type","person"])
speeds.loc[speeds["ws_type"]=="SUV", "avg_speed"] *= 33000/25000
speeds.loc[speeds["ws_type"]=="CC1", "avg_speed"] *= 33000/25000
view = speeds.loc[speeds.avg_speed < 2000]
sns.boxplot(x="ws_type", y="avg_speed", data=view, whis=np.inf)
#sns.stripplot(x="ws_type", y="avg_speed", data=view)
plt.xlabel("Windshield series")
plt.ylabel("Crack speed [m/s]")
plt.show()