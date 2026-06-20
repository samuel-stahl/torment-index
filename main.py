import argparse
import configparser
import os
from pathlib import Path
import pandas as pd
from functools import reduce

CONFIG_FILE = 'config.ini'
RESULTS_PATH = 'results'

RP_ERA_COEF = 1
OBP_COEF = 1
BSR_COEF = 8
SB_COEF = 0.5
BA_RISP_COEF = 3
BA_TWO_OUTS_COEF = 3
BA_TWO_OUTS_RISP_COEF = 4
OAA_COEF = 16


def get_year() -> str | None:
    """retrieves the desired year from the passed argument"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-y", "--year", help="desired year")
    return parser.parse_args().year


def calculate_era(sp_data: str, rp_data: str) -> pd.DataFrame:
    """returns starting and relief pitcher adjusted Earned-Run Average (ERA+) for all 30 teams"""
    sp_df = pd.read_csv(sp_data)
    rp_df = pd.read_csv(rp_data)

    total_sp_er_ip = sp_df.agg({"IP": "sum", "ER": "sum"})
    sp_avg_era = total_sp_er_ip['ER'] * 9 / total_sp_er_ip['IP']
    sp_df = sp_df.assign(sp_era_plus=sp_avg_era * 100 / sp_df['ERA'])

    total_rp_er_ip = rp_df.agg({"IP": "sum", "ER": "sum"})
    rp_avg_era = total_rp_er_ip['ER'] * 9 / total_rp_er_ip['IP']
    rp_df = rp_df.assign(rp_era_plus=rp_avg_era * 100 / rp_df['ERA'])

    return pd.merge(sp_df[['Team', 'sp_era_plus']], rp_df[['Team', 'rp_era_plus']], on="Team")


def calculate_standard_batting(data: str) -> pd.DataFrame:
    """calculates adjusted On-Base Percentage (OBP+), adjusted Slugging Percentage (SLG+),
    and adjusted Stolen Bases (SB+) for all 30 teams"""
    batting_df = pd.read_csv(data)
    avg_obp = batting_df.iloc[[30]]['OBP'].item()
    avg_slg = batting_df.iloc[[30]]['SLG'].item()
    avg_sb = batting_df.iloc[[30]]['SB'].item()

    batting_df = batting_df.assign(obp_plus=batting_df['OBP'] * 100 / avg_obp)
    batting_df = batting_df.assign(slg_plus=batting_df['SLG'] * 100 / avg_slg)
    batting_df = batting_df.assign(sb_plus=batting_df['SB'] * 100 / avg_sb)

    batting_df = batting_df.drop([30])

    return batting_df[['Team', 'obp_plus', 'slg_plus', 'sb_plus']]


def calculate_bsr(data: str) -> pd.DataFrame:
    """calculates Adjusted Base-running (BSR+) for all 30 teams"""
    bsr_df = pd.read_csv(data)
    by_team = bsr_df.groupby('Team').agg({"runner_runs": "sum"})
    total_bsr = bsr_df.agg({"runner_runs": "sum"})
    avg_bsr = total_bsr['runner_runs'] / 30
    by_team = by_team.assign(bsr_plus=(by_team['runner_runs'] - avg_bsr) + 100)

    return by_team['bsr_plus']


def calculate_clutch(risp_data: str, two_outs_data: str, two_outs_risp_data: str) -> pd.DataFrame:
    """calculates Adjusted Batting Average (BA+) with two outs, Runners in scoring position (RISP),
    and both for all 30 teams"""
    risp_df = pd.read_csv(risp_data)
    total_risp_stats = risp_df.agg({"AB": "sum", "H": "sum"})
    overall_risp_avg = total_risp_stats['H'] / total_risp_stats['AB']
    risp_df = risp_df.assign(ba_risp_plus=risp_df['BA'] * 100 / overall_risp_avg)

    two_outs_df = pd.read_csv(two_outs_data)
    total_two_outs_stats = two_outs_df.agg({"AB": "sum", "H": "sum"})
    overall_two_outs_avg = total_two_outs_stats['H'] / total_two_outs_stats['AB']
    two_outs_df = two_outs_df.assign(ba_two_outs_plus=two_outs_df['BA'] * 100 / overall_two_outs_avg)

    two_outs_risp_df = pd.read_csv(two_outs_risp_data)
    total_two_outs_risp_stats = two_outs_df.agg({"AB": "sum", "H": "sum"})
    overall_two_outs_risp_avg = total_two_outs_risp_stats['H'] / total_two_outs_risp_stats['AB']
    two_outs_risp_df = two_outs_risp_df.assign(ba_two_outs_risp_plus=two_outs_df['BA'] * 100 / overall_two_outs_risp_avg)

    dfs = [risp_df[['Team', 'ba_risp_plus']], two_outs_df[['Team', 'ba_two_outs_plus']],
           two_outs_risp_df[['Team', 'ba_two_outs_risp_plus']]]

    return reduce(lambda left, right: pd.merge(left, right, on=['Team'],
                                               how='outer'), dfs)


def calculate_oaa(data: str) -> pd.DataFrame:
    """roughly calculates adjusted Outs Above Average (OAA+) for all 30 teams"""
    oaa_df = pd.read_csv(data)
    oaa_total = oaa_df.groupby('Team').agg({'outs_above_average': 'sum'})
    oaa_total = oaa_total.assign(oaa_plus=oaa_total['outs_above_average'] + 100)
    return oaa_total['oaa_plus']


def calculate_torment_index(row: pd.Series) -> float:
    """calculates and returns the torment index for a given team based on the formula described in the README"""
    rp_era_factor = row['rp_era_plus'] * RP_ERA_COEF
    obp_plus_factor = row['obp_plus'] * OBP_COEF
    sb_plus_factor = row['sb_plus'] * SB_COEF
    bsr_plus_factor = row['bsr_plus'] * BSR_COEF
    ba_risp_factor = row['ba_risp_plus'] * BA_RISP_COEF
    ba_two_outs_factor = row['ba_two_outs_plus'] * BA_TWO_OUTS_COEF
    ba_two_outs_risp_factor = row['ba_two_outs_risp_plus'] * BA_TWO_OUTS_RISP_COEF
    oaa_factor = row['oaa_plus'] * OAA_COEF

    additive_portion = (rp_era_factor + obp_plus_factor + sb_plus_factor + bsr_plus_factor
                        + ba_risp_factor + ba_two_outs_factor + ba_two_outs_risp_factor + oaa_factor) / 100

    sp_era_mult = (100 - abs(100 - row['sp_era_plus'])) / 100
    slg_mult = (100 - abs(100 - row['slg_plus'])) / 100

    return additive_portion * sp_era_mult * slg_mult


def output_torment_index() -> None:
    """using input data provided in CONFIG_FILE, outputs the torment index and related statistics to CSV files in the file path specified by RESULTS_PATH. If a year
     is provided as a command line argument, only calculates the torment index for the specified year"""
    config = configparser.ConfigParser()
    if not os.path.isfile(CONFIG_FILE):
        config['EXAMPLE_YEAR'] = {
            'sp_era_file': '',
            'rp_era_file': '',
            'batting_file': '',
            'risp_file': '',
            'bsr_file': '',
            'oaa_file': '',
            'two_outs_file': '',
            'two_outs_risp_file': '',
        }
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        print('No config file found. '
              'Generating default. Copy this format for each additional year you would like to use.')
        exit()
    config.read(CONFIG_FILE)
    arg_year = get_year()

    for year in config:
        if (arg_year is not None and year != arg_year) or year == 'DEFAULT':
            # only run program for one year if it is specified in args,
            # otherwise run for all years present in config
            continue
        sp_era_file = config[year]['sp_era_file']  # by player, need to aggregate
        rp_era_file = config[year]['rp_era_file']  # by player, need to aggregate
        batting_file = config[year]['batting_file']  # includes OBP, SLG, SB
        bsr_file = config[year]['bsr_file']  # by player, need to aggregate
        risp_file = config[year]['risp_file']
        two_outs_file = config[year]['two_outs_file']
        two_outs_risp_file = config[year]['two_outs_risp_file']
        oaa_file = config[year]['oaa_file']  # by player, need to aggregate

        era = calculate_era(sp_era_file, rp_era_file)
        standard_batting = calculate_standard_batting(batting_file)
        bsr = calculate_bsr(bsr_file)
        clutch_stats = calculate_clutch(risp_file, two_outs_file, two_outs_risp_file)
        oaa = calculate_oaa(oaa_file)
        dfs = [era, standard_batting, bsr, clutch_stats, oaa]
        all_data = reduce(lambda left, right: pd.merge(left, right, on=['Team'],
                                                       how='outer'), dfs)

        all_data = all_data.assign(torment_index=all_data.apply(lambda row: calculate_torment_index(row), axis=1))

        Path(f'{RESULTS_PATH}/{year}').mkdir(parents=True, exist_ok=True)
        all_data.to_csv(f'{RESULTS_PATH}/{year}/{year}_full_results.csv', index=False)
        torment_index_only = all_data[['Team', 'torment_index']].sort_values(by=['torment_index'], ascending=False)
        torment_index_only.to_csv(f'{RESULTS_PATH}/{year}/{year}_torment_index.csv', index=False)
        print(f"Torment index calculated for {year}")


if __name__ == '__main__':
    output_torment_index()
