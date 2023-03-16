import plotly.express as px
import pandas as pd
import numpy as np


class AnalysisMethod:
    def __init__(self):
        pass
        

    def draw_path_figure(self, df):
        '''
        @draw fly path of AUV
        param:df ([x,y,z])
        '''
        df = np.array(df)
        plot ={'x':[],'y':[],'z':[],'path':'dron'}
        plot_UE4 = {'x':[0, 0, 0, 0, 0, 0, 16, 17.29, 17.29, 17.29],
                    'y':[0, 17.1, 17.1, 34.195, 34.195, 59.09, 59.09, 59.09, 59.09, 31.725],
                    'z':[2.5, 2.5, 4.5, 4.5, 2.5, 2.5, 2.5, 2.5, 5.5, 5.5],'path':'Origin'}
        plot['x'] = df[:,0]
        plot['y'] = df[:,1]
        plot['z'] = df[:,2]

        df1 = pd.DataFrame(plot_UE4)
        df2 = pd.DataFrame(plot)
        DataFrame = pd.concat ([df1,df2],axis=0,ignore_index=True)
        fig = px.line_3d(DataFrame, x="x", y="y", z="z",color='path')
        fig.show()


Analysis = AnalysisMethod()

subject = 'cwz'
runloop = 'Asy_07'
filename = subject + '_' + runloop
df = np.load('./data/' + filename+'/PathData.npy')

Analysis.draw_path_figure(df)
