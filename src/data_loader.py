import pandas as pd
def load_data():
    menus = pd.read_csv('data/menus.csv')
    logs = pd.read_csv('data/logs.csv')
    return menus, logs