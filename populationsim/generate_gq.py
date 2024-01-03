import pandas as pd


from activitysim.core import inject
from activitysim.core import config
from activitysim.core import input


from activitysim.cli.run import handle_standard_args

"""
    Reads the GQ seed and control totals 
"""
def read_tables(gq_options):

    gq_table_list = gq_options.get('input_table_list', None)

    print("+++ Reading input tables ------------------")
    input_dfs = {}
    for table_info in gq_table_list:
        tablename = table_info.get('tablename')
        input_dfs[tablename] = input.read_from_table_info(table_info)
        #print(f"+++ Reading table {tablename} with shape {input_dfs[tablename].shape}")
    



    return input_dfs

#--------------------------------------------------------------------------------------------------

"""
    Loops over each GQ type and generates GQ synpop
"""
def draw_gqpopulation(gq_options, input_dfs):

    # GQ column in seed
    print("+++ Generating GQ syn pop ------------------")
    gqType_column = gq_options.get('GQ_type_column')

    # GQ map between GQtype_code and control column
    gq_map = gq_options.get('GQ_control_map')
    gq_seed = gq_options.get('random_seed')
    hh_id_col = gq_options.get('household_id_col')
    hh_wt_col = gq_options.get('household_weight_col')

    # Initializing the synthetic GQ populations
    gq_hhs = None

    # Assinging to new variables  (incase we change organization later)
    hhgqseed_df = input_dfs['households']
    pergqseed_df = input_dfs['persons']
    controls_df = input_dfs['mgra_control_data']
    geo_df = input_dfs['geo_cross_walk']

    # Looping over gq types
    for gq in gq_map:
        gq_code, gq_control = gq['code'], gq['control_column']
        #print(f'+++ drawing GQ_type {gq_code}')


        # getting the tazs with GQ controls
        gq_controls = controls_df.loc[controls_df[gq_control] > 0, ['mgra', gq_control]].copy()
        gq_controls = pd.merge(gq_controls, geo_df, on = 'mgra', how = 'left')
        #print("gq_controls shape: ", gq_controls.shape)
        
        # getting seed samples for the GQ type
        hh_sample = hhgqseed_df[hhgqseed_df[gqType_column] == gq_code].copy()
        per_sample = pergqseed_df[pergqseed_df[hh_id_col].isin(hh_sample[hh_id_col])].copy()
        #print(f"seed shapes hh: {len(hh_sample)} per: {len(per_sample)}")


        # getting the control_total for each mgra
        for index, crow in gq_controls.iterrows():
            mgra, puma, ndraws = crow['mgra'], crow['PUMA'], crow[gq_control]
            #print(f"++ TAZ: {taz} PUMA: {puma}")
            taz_hhs = hh_sample[hh_sample['PUMA'] == puma]
            # case where sample has too few in the corresponding PUMA
            if len(taz_hhs) < 200:
                taz_hhs = hh_sample
            # drawing hhs
            hhdraw = taz_hhs.sample(n = ndraws, 
                                replace = True, 
                                weights = taz_hhs[hh_wt_col].values, 
                                random_state = gq_seed)
            
            hhdraw['mgra'] = mgra
            # Adding drawn hhs to synth pop
            if gq_hhs is None:
                gq_hhs = hhdraw.copy()
            else:
                gq_hhs = pd.concat([gq_hhs, hhdraw])


    # Genrateing household_id and getting corresponding persons
    gq_hhs = gq_hhs.reset_index(drop = True)
    gq_hhs['household_id'] = range(1, len(gq_hhs)+1)
    gq_pers = pd.merge(gq_hhs[['household_id', 'mgra', hh_id_col]], pergqseed_df, 
                    on = hh_id_col, how = 'left')
    
    #print("gq_hhs : \n ", gq_hhs.head())
    #print("gq_pers: \n ", gq_pers.head())

    synpop_dfs = {'households': gq_hhs,
                  'persons': gq_pers}

    return synpop_dfs

#--------------------------------------------------------------------------------------------------

"""
    The control columns are adjusted to reflect the generated GQ population
    WE DO NOT USE IT NOW!
"""
def adjust_controls(gq_options, input_dfs, synpop_dfs):

    adjust_columns = gq_options.get('adjust_columns', None)
    persons = synpop_dfs['persons']
    households = synpop_dfs['households']

    controls_df = input_dfs['mgra_control_data']
    outcontrols_df = controls_df.copy()


    target_dfs = {'persons': persons['mgra'].to_frame(),
                  'households': households['mgra'].to_frame()
                }   

    if adjust_columns:
        for adj_col in adjust_columns:
            assert len(adj_col) == 1, "We expect only columns adjustment at a time"
            for target, express in adj_col.items():
                if 'persons' in express:
                    target_dfs['persons'][target] = pd.eval(express)
                elif 'households' in express:
                    target_dfs['households'][target] = pd.eval(express)

    for k, df in target_dfs.items():
        if len(df) > 0:
            generated_totals = df.groupby('mgra').sum()
            #print('+++ generated_totals shape: ', generated_totals.shape)
            #print(generated_totals.head())
            outcontrols_df = pd.merge(outcontrols_df, generated_totals, how = 'left', left_on = 'mgra', right_index = True,
                                    suffixes=('', '_adj')).fillna(0)
            # substracting the specific control totals
            for col in generated_totals.columns:
                #print(f"col: {col}, cont: {outcontrols_df[col].sum()}, adj: {outcontrols_df[col + '_adj'].sum()}")
                outcontrols_df[col] = outcontrols_df[col] - outcontrols_df[col + '_adj']
            # getting rid of the added columns
            outcontrols_df.drop(columns = [item + '_adj' for item in generated_totals.columns], inplace = True)


    return outcontrols_df
    

    # print("controls_df sums: ", controls_df.sum())
    # print("outcontrols_df sums: ", outcontrols_df.sum())

#--------------------------------------------------------------------------------------------------

def write_outputs(gq_options, synpop_dfs):

    # # Writing out the adjusted controls
    # outcontrol_fname = gq_options.get('output_control_file')
    # outcontrols_df.to_csv(outcontrol_fname, index = False)

    # Writing out synthetici poplulation
    output_config = gq_options.get('output_gq_population')
    household_id = output_config['household_id']

    # Writing out households
    for tbl in synpop_dfs.keys():
        tbl_config = output_config[tbl]
        print(f"+++ Writing out {tbl} --------")
        if tbl == 'households':
            cols = [household_id, 'PUMA', 'mgra'] + tbl_config['columns']
        else:
            cols = [household_id, 'PUMA', 'mgra'] + tbl_config['columns']


        synpop_dfs[tbl][cols].to_csv(tbl_config['filename'], index = False)
    


#--------------------------------------------------------------------------------------------------

def run_gq(args):

    handle_standard_args(args)  # possibly update injectables
    gq_options = config.setting('gq_options', None)
    #print("gq_options: ", gq_options)

    input_dfs = read_tables(gq_options)

    synpop_dfs = draw_gqpopulation(gq_options, input_dfs)

    #outcontrols_df = adjust_controls(gq_options, input_dfs, synpop_dfs)

    write_outputs(gq_options, synpop_dfs)

    print("+++ Finished writing out the GQ synpop ----------")





