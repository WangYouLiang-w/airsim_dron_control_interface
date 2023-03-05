import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
plot_UE4 = {'x':[0, 0, 0, 0, 0, 0, 16, 17.29, 17.29, 17.29],
            'y':[0, 17.1, 17.1, 34.195, 34.195, 59.09, 59.09, 59.09, 59.09, 31.725],
            'z':[2.5, 2.5, 4.5, 4.5, 2.5, 2.5, 2.5, 2.5, 5.5, 5.5],'path':'Origin'}

plot_UE = {'x':[0, 0, 0, 0, 0, 0, 16, 17.29, 17.29, 0],
            'y':[0, 17.1, 17.1, 34.195, 34.195, 59.09, 59.09, 59.09, 59.09, 31.725],
            'z':[2.5, 2.5, 4.5, 4.5, 2.5, 2.5, 2.5, 2.5, 5.5, 5.5],'path':'dron'}
df1 = pd.DataFrame(plot_UE4)
df2 = pd.DataFrame(plot_UE)
# df = px.data.gapminder().query("continent=='Europe'")
# print(type(df))
df=pd.concat ([df1,df2],axis=0,ignore_index=True)
# fig1 = px.line_3d(plot_UE4, x="x", y="y", z="z", color='path')
print(df)
fig = px.line_3d(df, x="x", y="y", z="z", color='path')

# fig = [fig1,fig2]
fig.show()