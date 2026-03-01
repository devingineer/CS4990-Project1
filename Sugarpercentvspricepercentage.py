import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
3
# load data set 
path = r"C:\Users\romod\Downloads\candy-data.csv"
df = pd.read_csv(path)

# low medium high sugar sections 

bins = [0.0, 0.33, 0.66, 1.0]
sLabel = ["low Sugar", "Medium Sugar", "High Sugar"]

df ["Sbin"] = pd.cut (
    df["sugarpercent"],
    bins=bins,
    labels = sLabel,
    include_lowest = True, 
)

# averaging price per sugar 

Pmean = (
    df.groupby("Sbin", observed=True) ["pricepercent"]
    .mean()
    .reindex(sLabel)
)

# Graph 1: Bar Chart 

graph1, axis1 = plt.subplots(figsize=(8, 4.8))
axis1.bar (Pmean.index.astype(str),Pmean.values, color="steelblue")
axis1.set_title("Average Price by Sugar Content")
axis1.set_xlabel("Sugar Content (compared to other candies)")
axis1.set_ylabel("Avererage Price Percentage\n 0 = cheapest, 1 = most expensive)")
axis1.set_ylim(0,1)

axis1.grid(False)
for spine in axis1.spines.values():
    spine.set_visible(False)
axis1.tick_params(axis="both", length=0)

graph1.tight_layout()

# Graph 2:  Bar Chart with Lines 

graph2, axis2= plt.subplots(figsize=(8, 4.8))
axis2.bar (Pmean.index.astype(str),Pmean.values, color="steelblue")
axis2.set_title("Average Price by Sugar Content")
axis2.set_xlabel("Sugar Content (compared to other candies)")
axis2.set_ylabel("Avererage Price Percentage\n 0 = cheapest, 1 = most expensive)")
axis2.set_ylim(0,1)

axis2.set_axisbelow(True)
axis2.grid(True, axis="y", linestyle="-.", alpha= 1)
graph2.tight_layout()

# Graph 3: Price Tier Groups 

graph2, axis2= plt.subplots(figsize=(8, 4.8))
axis2.bar (Pmean.index.astype(str),Pmean.values, color="steelblue")
axis2.set_title("Average Price by Sugar Content")
axis2.set_xlabel("Sugar Content (compared to other candies)")
axis2.set_ylabel("Avererage Price Percentage\n 0 = cheapest, 1 = most expensive)")
axis2.set_ylim(0,1)

axis2.set_axisbelow(True)
axis2.grid(True, axis="x", linestyle="-.", alpha= 1)
graph2.tight_layout()

plt.show()