import os
import yaml

"""
Usage:

```
conda activate dimet
cd $HOME


snakemake -s Snaketoy0.smk --cores 1 --config PRIMARY_CONFIG="~/toy0/analys01/config-0-0.yml"
METABOLOGRAM_CONFIG="~/toy0/analys01/metabologram_config.yml" --latency-wait 15

```

"""

def open_config_file_snake_version(confifile):
    try:
        with open(confifile, "r") as f:
            confidic = yaml.load(f, Loader=yaml.Loader)
    except yaml.YAMLError as yam_err:
        print(yam_err)
        print("\nimpossible to read configuration file")
        confidic = None
    except Exception as e:
        print(e)
        print("\nimpossible to read configuration file")
        confidic = None

    return confidic



primary_config_path = os.path.expanduser(config["PRIMARY_CONFIG"])

primary_config = open_config_file_snake_version(primary_config_path)

outdir = os.path.expanduser(primary_config['out_path'])

try:
    metabolog_config_path = os.path.expanduser(config["METABOLOGRAM_CONFIG"])
    metabologram_config = open_config_file_snake_version(metabolog_config_path)
except:
    metabologram_config = None



rule all:
    input:
        f'{primary_config_path}',
        f'{outdir}results/prepared_tables/prep.log' ,
        f'{outdir}results/plots/log/pca.log',
        f'{outdir}results/differential_analysis/diff.log',
         f'{outdir}results/plots/log/bars.log',
        f'{outdir}results/plots/log/metabologram.log'
    output:        
        f'{outdir}results/plots/log/end.log'




rule prepare:
    input:
        f'{primary_config_path}'
    output :
        f'{outdir}results/prepared_tables/prep.log'
    shell:
        f"python -m DIMet.src.prepare {primary_config_path} > {outdir}results/prepared_tables/prep.log"



rule pca:
    input:
         f'{primary_config_path}',
         f'{outdir}results/prepared_tables/prep.log'
    log:
        f'{outdir}results/plots/log/pca.log'

    shell:
         f"python -m DIMet.src.pca {primary_config_path} --draw_ellipses > {outdir}results/plots/log/pca.log"



rule differential:
    input:
         f'{primary_config_path}',
          f'{outdir}results/prepared_tables/prep.log'
    log:
         f'{outdir}results/differential_analysis/diff.log'

    shell:
         f"python -m DIMet.src.differential_analysis {primary_config_path} --no-isotopologues \
            > {outdir}results/differential_analysis/diff.log"


rule bars:
    input:
         f'{primary_config_path}',
         f'{outdir}results/prepared_tables/prep.log'
    log :  
          f'{outdir}results/plots/log/bars.log'
    
    shell:
        #f"python -m DIMet.src.abundances_bars --help > {outdir}results/plots/log/bars.log"
        f"python -m DIMet.src.abundances_bars {primary_config_path} > {outdir}results/plots/log/bars.log"



rule metabologram:
    input:
        f'{metabolog_config_path}',
        f'{outdir}results/prepared_tables/prep.log',
        f'{outdir}results/differential_analysis/diff.log'
    log:
         f'{outdir}results/plots/log/metabologram.log'

    shell:
         f"python -m DIMet.src.metabologram {metabolog_config_path} > {outdir}results/plots/log/metabologram.log"

	

rule end:
    input:
         f'{primary_config_path}',
         f'{outdir}results/prepared_tables/prep.log',
         f'{outdir}results/differential_analysis/diff.log',
            f'{outdir}results/plots/log/bars.log',
            f'{outdir}results/plots/log/metabologram.log'

    output:
        f'{outdir}results/plots/log/end.log'

    shell:
         f"echo 'ended dimet with snakemake' > {outdir}results/plots/log/end.log"


# END

# Print DAG:
# conda install -c conda-forge python-graphviz
# snakemake -s mintool_snake/Snakefile.smk --cores 1
# --configfiles mintask_in_out/uconf_a/uconf_a.yml mintask_in_out/snake_config.yml
    # --config ADVANCED= --dag | dot -Tpdf > dag.pdf
