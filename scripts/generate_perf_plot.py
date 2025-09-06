import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import sqlitecloud
import datetime
import seaborn as sns
def adapt_datetime(val):
    """Convert datetime.datetime object to ISO 8601 string."""
    return val.isoformat()

def convert_datetime(val):
    """Convert ISO 8601 string to datetime.datetime object."""
    return datetime.datetime.fromisoformat(val.decode())

sqlitecloud.register_adapter(datetime.datetime, adapt_datetime)
sqlitecloud.register_converter("datetime", convert_datetime)

con = sqlitecloud.connect("sqlitecloud://calrr1x5hz.g2.sqlite.cloud:8860/model_perf?apikey=sgqjlGAUV3gGHvF3lsOsJAlk0lAF0j0URQUAJf9vQAY")
df = pd.read_sql_query("SELECT * FROM model_perf ORDER BY date", con)
con.close()


df["date"] = pd.to_datetime(df["date"])
# Plot

plt.figure(figsize=(10, 6))
sns.lineplot(data=df, x="date", y="F1_SCORE", marker="o")
plt.title("Historique des performances du modèle")
plt.xlabel("Date")
plt.ylabel("F1 Score")
plt.tight_layout()

# Sauvegarde du graphe
plt.savefig("model_performance.png")
plt.close()