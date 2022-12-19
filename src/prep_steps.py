#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 17 20:38:00 2022

@author: johanna
"""

import os

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def extrudf2dico(extrudf):
    extruD = dict()
    for i, r in extrudf.iterrows():
        metaboliteok = r["metabolite"].replace('"', "")
        if r["compartment"] not in extruD.keys():
            extruD[r["compartment"]] = [metaboliteok]
        else:
            extruD[r["compartment"]].append(metaboliteok)
    return extruD


def detectifinbadlist(al_, amet, style):
    if style == "VIB":
        amet = amet.replace("_PARENT", "")
        amet = amet.split("_C13-label-")[0]
    if style == "generic":
        amet = amet.split("_label")[0]

    if amet in al_:
        return 0
    else:
        return 1

def detectifinbadlistB(al_, amet):
    amet = amet.split("_m+")[0]
    if amet in al_:
        return 0
    else:
        return 1


def transformmyisotopologues(dfrownames_, style):
    if style == "VIB":
        outli_ = list()
        for ch in dfrownames_:
            if "_C13-label-" in ch:
                elems = ch.split("_C13-label-")
                metabolite = elems[0]
                species = "m+{}".format(elems[-1].split("-")[-1])
            elif "_PARENT" in ch:
                elems = ch.split("_PARENT")
                metabolite = elems[0]
                species = "m+0"
            else:
                metabolite = ch
                species = "m+?"
            outli_.append(metabolite + "_" + species)
    elif style == "generic":
        outli_ = [i.replace("label", "m+") for i in dfrownames_]
    return outli_



def stomp_neg_andsuperiorto1(df):
    df[df < 0] = 0
    df[df > 1] = 1
    return df


def quality_control(dfco, metadata, co):
    """
    replaces untrustful zeroes by NaN, example:
        [value 0 0] -> [value NaN NaN]
        [0 value value] -> [NaN value value]

    """
    metadataco = metadata.loc[metadata["short_comp"] == co, :]
    metadataco = metadataco.assign(s = metadataco['sample'].str.split("-", regex=False).str[0])
    #print(metadataco.short_comp.unique(), "  <======")
    grouping_df = metadataco[['sample', 's']]
    tmpD = dict()
    for gro in grouping_df['s'].unique():
        colshere = grouping_df.loc[grouping_df['s'] == gro, "sample"]
        tmpdf = dfco[colshere]
        t2 = tmpdf.copy()
        for i, row in tmpdf.iterrows():
            vec = tmpdf.loc[i]

            n_zeros =  len(vec) - np.count_nonzero(vec)
            if (n_zeros > 0) and (n_zeros < len(vec)):
                # minimum 1 and maximum n-1 values are different from zero
                res = np.array(vec)
                res[res == 0] = 'NaN'  # replace by nan if  all replicates not zero
            else:
                res = np.array(vec)

            t2.loc[i] = res
             # end for i,r
        tmpD[gro] = t2
        # end for gro
    o_df = pd.concat(tmpD.values(), axis = 1, ignore_index=False)
    return o_df


def save_new_dfsB( datadi, names_compartments, filename, metadata, extrudf,
                  diroutput, style, stomp_values, UNDER_THIS_SETZERO ):
    extruD = extrudf2dico(extrudf)

    pre_met_or_iso_df = pd.read_csv(datadi + filename, sep="\t", index_col=0)

    if "isotopolo" in filename.lower():
        print(pre_met_or_iso_df.head())
        # transform isotopologue table style in m+x style
        newindex = transformmyisotopologues(pre_met_or_iso_df.index, style)
        pre_met_or_iso_df.index = newindex
        pre_met_or_iso_df[pre_met_or_iso_df < UNDER_THIS_SETZERO] = 0
        if stomp_values == "Y":
            pre_met_or_iso_df = stomp_neg_andsuperiorto1(pre_met_or_iso_df)

    if "rawintensity" in filename.lower():
        print(pre_met_or_iso_df.head(9))
        newindex = transformmyisotopologues(pre_met_or_iso_df.index, style)
        pre_met_or_iso_df.index = newindex


    if "frac" in filename.lower() and "contrib" in filename.lower():
        pre_met_or_iso_df[pre_met_or_iso_df < UNDER_THIS_SETZERO] = 0
        if stomp_values == "Y":
            pre_met_or_iso_df = stomp_neg_andsuperiorto1(pre_met_or_iso_df)


    for compartment in names_compartments.values():
        f_o = filename.split(".")[0] + "_" + compartment + ".tsv"

        # using metadata, to set apart (met_or_iso_df) compartment specific samples
        samplestokeep_= metadata.loc[metadata["short_comp"] == compartment,'sample']
        met_or_iso_df = pre_met_or_iso_df[[ k for k in samplestokeep_]]

        # create column to mark rows to delete
        # met_or_iso_df['todelete'] = np.nan
        met_or_iso_df = met_or_iso_df.assign(todelete=np.nan)
        for i, r in met_or_iso_df.iterrows():
            # print(i) # i is the i metabolite ....
            #hereboolnum = detectifinbadlist(extruD[compartment], i, style)
            hereboolnum = detectifinbadlistB(extruD[compartment], i)
            met_or_iso_df.loc[i, "todelete"] = hereboolnum
            # = hereboolnum # 0 or 1
        # end for iterrows
        # met_or_iso_df.todelete.value_counts() # visualize "table" on 'todelete' colummn
        met_or_iso_df_o = met_or_iso_df[met_or_iso_df["todelete"] != 0]
        met_or_iso_df_o = met_or_iso_df_o.drop(columns=["todelete"])

        #met_or_iso_df_o.to_csv(diroutput + f_o.replace(".tsv","") +"_original.tsv", sep="\t")
        # new : quality_control

        met_or_iso_df_o = quality_control(met_or_iso_df_o, metadata, compartment)

        met_or_iso_df_o.to_csv(diroutput + f_o, sep="\t")
    # end for
    return 0


def add_metabolite_column(df):
    theindex = df.index
    themetabolites = [i.split("_m+")[0] for i in theindex]
    df = df.assign(metabolite=themetabolites)

    return df


def add_isotopologue_type_column(df):
    theindex = df.index
    preisotopologue_type = [i.split("_m+")[1] for i in theindex]
    theisotopologue_type = [int(i) for i in preisotopologue_type]
    df = df.assign(isotopologue_type=theisotopologue_type)

    return df


def save_heatmap_sums_isos(thesums, figuretitle, outputfigure):
    fig, ax = plt.subplots( figsize=(9,10))
    sns.heatmap(thesums,
                annot=True, fmt=".1f", cmap="crest",
                square = True,
                annot_kws = {
                    'fontsize' : 6
                },
                ax= ax)
    plt.xticks(rotation=90)
    plt.title(figuretitle)
    plt.savefig(outputfigure)
    plt.close()

    return 0


def givelevels(melted):
    another = melted.copy()
    another = another.groupby('metabolite').min()
    another = another.sort_values(by='value', ascending=False)
    levelsmetabolites = another.index
    tmp = melted['metabolite']
    melted['metabolite'] = pd.Categorical(tmp, categories=levelsmetabolites)

    return melted


def table_minimalbymet(melted, fileout):
    another = melted.copy()
    another = another.groupby('metabolite').min()
    another = another.sort_values(by='value', ascending=False)
    another.to_csv(fileout, sep='\t', header=True)


def save_rawisos_plot(dfmelt, figuretitle, outputfigure):
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    sns.stripplot(ax=ax, data=dfmelt, x="value", y="metabolite", jitter=False,
                  hue="isotopologue_type", size=4, palette="tab20")
    plt.axvline(x=0,
                ymin=0,
                ymax=1,
                linestyle="--", color="gray")
    plt.axvline(x=1,
                ymin=0,
                ymax=1,
                linestyle="--", color="gray")
    sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))
    plt.title(figuretitle)
    plt.xlabel("fraction")
    plt.savefig(outputfigure)
    plt.close()
    return 0




# def save_new_dfs( datadi, names_compartments, filename,
#                   metadata, extrudf, diroutput, style ):
#     extruD = extrudf2dico(extrudf)
#     met_or_iso_df = pd.read_csv(datadi + filename, sep="\t", index_col=0)
#
#     for compartment in names_compartments.values():
#         f_o = filename.split(".")[0] + "_" + compartment + ".tsv"
#
#         # using metadata, to set apart (met_or_iso_df) compartment specific samples
#         samplestokeep = metadata.loc[metadata["short_comp"] == compartment, "sample"]
#         met_or_isosplit_mspecies_files_df = met_or_iso_df[samplestokeep]
#
#         # create column to mark rows to delete
#         # met_or_iso_df['todelete'] = np.nan
#         met_or_iso_df = met_or_iso_df.assign(todelete=np.nan)
#         for i, r in met_or_iso_df.iterrows():
#             # print(i) # i is the i metabolite ....
#             hereboolnum = detectifinbadlist(extruD[compartment], i, style)
#             # print(hereboolnum)
#             met_or_iso_df.loc[i, "todelete"] = hereboolnum
#             # = hereboolnum # 0 or 1
#         # end for iterrows
#         # met_or_iso_df.todelete.value_counts() # visualize "table" on 'todelete' colummn
#         met_or_iso_df_o = met_or_iso_df[met_or_iso_df["todelete"] != 0]
#         met_or_iso_df_o = met_or_iso_df_o.drop(columns=["todelete"])
#         met_or_iso_df_o.to_csv(diroutput + f_o, sep="\t")
#     # end for
#     return 0
