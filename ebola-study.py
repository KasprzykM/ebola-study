import json
from pymongo import MongoClient
import numpy as np
import matplotlib.pyplot as plt

from WeeklyData import WeeklyData
from epidemic_models import SIR

DATABASES = {
    'Guinea': ['guinea_weekly.json',
               'guinea_conarky_weekly.json',
               'guinea_district_weekly.json'],

    'Liberia': ['liberia_weekly.json',
                'liberia_monsterrado_weekly.json',
                'liberia_district_weekly.json'],

    'Sierra_Leone': ['sierra_weekly.json',
                     'sierra_westernarea_weekly.json',
                     'sierra_district_weekly.json']
}

DATA_SOURCES = ['Situation report', 'Patient database']

HIST_SIZE = (16, 9)
HIST_FONT_SIZE = 30
HIST_LABEL_SIZE = 7
HIST_BAR_WIDTH = 0.35


def create_hist_from_weekly(parsed_data):
    title = parsed_data.country_name
    title += ' ' + parsed_data.location if parsed_data.location is not None else ''

    index = np.arange(len(parsed_data.probable))

    bar_width = HIST_BAR_WIDTH

    fig, ax = plt.subplots(figsize=HIST_SIZE)

    probable = ax.bar(index, [dic['value'] for dic in parsed_data.probable]
                      , bar_width, label='Probable cases')
    confirmed = ax.bar(index + bar_width, [dic['value'] for dic in parsed_data.confirmed]
                       , bar_width, label='Confirmed cases')

    ax.set_title(title, fontsize=HIST_FONT_SIZE)
    ax.set_xlabel('Weeks', fontsize=HIST_FONT_SIZE)
    ax.set_ylabel('Value', fontsize=HIST_FONT_SIZE)
    ax.set_xticks(index + bar_width / 2)
    ax.set_xticklabels([dic['week'] for dic in parsed_data.probable], fontsize=HIST_LABEL_SIZE, rotation=90)
    ax.legend(fontsize=HIST_FONT_SIZE)
    paint_rectangle_values(probable)
    paint_rectangle_values(confirmed)
    plt.show()


def paint_rectangle_values(data, plt):
    for rectangle in data:
        height = rectangle.get_height()
        if height == 0:
            continue
        plt.annotate('{}'.format(height),
                     xy=(rectangle.get_x() + rectangle.get_width() / 2, height),
                     xytext=(0, 2),
                     textcoords="offset points",
                     ha='center', va='bottom')


def epidemic_models():
    sir_non_vital = SIR(population=12720001, days=861,
                        contact_rate=0.2, mean_recovery_rate=1. / 10)
    sir_non_vital.calculate_non_vital_SIR()
    sir_non_vital.plot_result(magnitude=1000)

    sir_vital = SIR(population=12720000, days=861,
                    contact_rate=0.2, mean_recovery_rate=1. / 10,
                    death_rate=8.7, birth_rate=37.2)
    sir_vital.calculate_vital_SIR()
    sir_vital.plot_result(magnitude=1000)


if __name__ == '__main__':
    with open('db_auth.json') as json_file:
        auth_data = json.load(json_file)
        client = MongoClient(auth_data['client_string'])

    weeklies_list = []
    guinea_list = []
    liberia_list = []
    sierra_list = []
    for country in DATABASES:
        summaries = client[country]
        for document in DATABASES[country]:
            doc_data = summaries[document]
            if 'district' in document:
                pass  # TODO: Depracated parsing with districs.
            else:
                weekly_data = WeeklyData(weekly_report=doc_data.find().next(),
                                         country_name=country,
                                         interval=2)
                if country == 'Guinea':
                    guinea_list.append(weekly_data)
                elif country == 'Sierra_Leone':
                    sierra_list.append(weekly_data)
                elif country == 'Liberia':
                    liberia_list.append(weekly_data)
                weeklies_list.append(weekly_data)
                create_hist_from_weekly(parsed_data=weekly_data)
                if weekly_data.location is None:  # Add only countries summary, excluding capital cities.
                    weeklies_list.append(weekly_data)
    guinea_sum = WeeklyData.sum_all_weekly(guinea_list, country_name="Guinea Sum")
    liberia_sum = WeeklyData.sum_all_weekly(liberia_list, country_name="Liberia Sum")
    sierra_sum = WeeklyData.sum_all_weekly(sierra_list, country_name="Sierra Leone Sum")
    epidemic_models()
    client.close()
