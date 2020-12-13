from api_config import *
import requests
import time
import json
from datetime import datetime
import os

header = {
"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
"X-Requested-With": "XMLHttpRequest"
} 

log_datetime_format = "%A, %d. %B %Y %I:%M:%S %p"
data_date_format = "%Y-%m-%d"

def default(obj):
    """Default JSON serializer."""
    import calendar, datetime

    if isinstance(obj, datetime.datetime):
        if obj.utcoffset() is not None:
            obj = obj - obj.utcoffset()
        millis = int(
            calendar.timegm(obj.timetuple()) * 1000 +
            obj.microsecond / 1000
        )
        return millis
    raise TypeError('Not sure how to serialize %s' % (obj,))


def process_report_date(report_date):
    report_date_str = ""
    for c in report_date:
        if c =='/' or c.isnumeric():
            report_date_str += c  
    return report_date_str


def get_all_cases():
    data_obj = {}
    print("get_all_cases start :" + time.strftime(log_datetime_format))
    response = requests.get(url_for_all_cases,data = data_obj)
    print("get_all_cases end :" + time.strftime(log_datetime_format))
    json_data = response.json()
    return json_data


def get_day_summary():
    data_obj = {}
    response = requests.get(url_for_day_summary,data = data_obj)
    json_data = response.json()
    return json_data  


def get_related_buildings():
    data_obj = {}
    response = requests.get(url_for_related_building,data = data_obj)
    json_data = response.json()
    return json_data

def refresh_data():
    print("refresh_data start :" + time.strftime(log_datetime_format))
    cases = get_all_cases()
    case_list = []
    for case in cases:
        report_date_str = process_report_date(case[report_date_key])
        case_list.append({'caseNo':int(case[case_no_key]),
        'reportDate':int(json.dumps(datetime.strptime(report_date_str, data_format).replace(hour=0, minute=0, second=0, microsecond=0), default=default)),
        'onsetDate':case[onset_date_key],
        'gender':case[gender_key],
        'age':int(case[age_key]),
        'admittedHospital':case[admitted_hospital_key],
        'hospitalStatus':case[hospital_status_key],
        'isHKResident':case[is_hk_resident_key],
        'caseClassification':case[case_classification_key],
        'status':case[status_key]})  
    insert_case_url = os.environ.get('INSERT_CASE_URL')
    if(insert_case_url is None):
        insert_case_url = 'http://localhost:8091/hkcovid19case/addMultiple'
    res = requests.post(insert_case_url, json=case_list, headers=header)
    print(res.text)       

    day_summarys = get_day_summary()
    day_summarys_list = []
    for day_summary in day_summarys:
        day_summarys_list.append({'asOfDate': day_summary[as_of_date_key],
        'noOfConfirmedCases': day_summary[no_of_confirmed_cases_key],
        'noOfRuledOutCases': day_summary[no_of_ruled_out_cases_key],
        'noOfCasesStillHospitalisedForInvestigation': day_summary[no_of_cases_still_hospitalised_for_investigation_key],
        'noOfCasesFulfillingTheReportingCriteria': day_summary[no_of_cases_fulfilling_the_reporting_criteria_key],
        'noOfDeathCases' :  day_summary[no_of_death_cases_key],
        'noOfDischargeCases' : day_summary[no_of_discharge_cases_key],
        'noOfProbableCases' : day_summary[no_of_probable_cases_key],
        'noOfHospitalisedCasesInCriticalCondition' : day_summary[no_of_hospitalised_cases_in_critical_condition_key]
        })
    insert_cases_summary_url = os.environ.get('INSERT_CASES_SUMMARY_URL')
    if(insert_cases_summary_url is None):
        insert_cases_summary_url = 'http://localhost:8091/hkcovid19casessummary/addMultiple'
    res = requests.post(insert_cases_summary_url, json=day_summarys_list, headers=header)
    print(res.text)

    related_buildings = get_related_buildings()
    related_buildings_list = []
    for related_building in related_buildings:

        no_of_case = 0
        related_case_str = related_building[related_case_key]
        if(len(related_case_str) > 0):
            no_of_case = len(related_case_str.split(","))
        related_case = []
        related_case_oth = None
        for n in related_case_str.split(","):
            if n.isnumeric():
                related_case.append(n)
            else:
                if related_case_oth is not None:
                    related_case_oth += ","
                    related_case_oth += n
                else:
                    related_case_oth = n ;  
        related_buildings_list.append({
        'asOfDate': int(json.dumps(datetime.today().replace(hour=0, minute=0, second=0, microsecond=0), default=default)),
        'district': related_building[district_key],
        'buildingName':related_building[building_name_key],
        'lastDateOfResidenceOfTheCase': related_building[last_date_of_residence_of_the_case_key],
        'relatedCase': related_case, 
        'noOfCase': no_of_case,
        'relatedCaseOth':related_case_oth
        })

    insert_related_building_url = os.environ.get('INSERT_RELATED_BUILDING_URL')
    if(insert_related_building_url is None):
        insert_related_building_url = 'http://localhost:8091/hkcovid19caserelatedbuilding/addMultiple'

    res = requests.post(insert_related_building_url, json=related_buildings_list, headers=header)
    print(res.text)
    print("refresh_data end :" + time.strftime(log_datetime_format))

refresh_data()