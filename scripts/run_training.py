import papermill as pm
import json
import os
import yaml
from pprint import pprint
from datetime import datetime
from PyInquirer.prompt import prompt
from PyInquirer import print_json
RUN_CODE = True
DEBUG = True

def exec_pm(*args, **kwargs):
    debug = kwargs.pop("debug", False)
    if debug:
        # pprint(f"env: EOG_USER {os.environ.get('EOG_USER','None')} EOG_PASSWORD {os.environ.get('EOG_PASSWORD','None')}")
        # pprint(f"args: {json.dumps(args)}\n kwargs: {json.dumps(kwargs)}")
        # print_json(dict(environ=dict(EOG_USER=os.environ.get('EOG_USER',None), EOG_PASSWORD=os.environ.get('EOG_PASSWORD',None))))
        # print_json(dict(args=args))
        # print_json(dict(kwargs=kwargs))
        return None
    return pm.execute_notebook(*args, **kwargs)


def main():
    if not RUN_CODE:
        print("Hello, run rollout world!")
        return

    print("Rolling out!")

    with open("scripts/config.yaml") as f:
        config = yaml.load(f,Loader=yaml.SafeLoader)
    country_name = "",
    rollout_date = "",
    notebook_type = "single_country",
    country_code = "",
    model_gdrive_url = "",
    country_osm = "",
    dhs_dta_prefix = "",
    dhs_geo_prefix = "",

    orig_answers = dict(
        country_name = country_name,
        rollout_date = rollout_date,
        notebook_type = notebook_type,
        country_code = country_code,
        model_gdrive_url = model_gdrive_url,
        country_osm = country_osm,
        dhs_dta_prefix = dhs_dta_prefix,
        dhs_geo_prefix = dhs_geo_prefix,
    )
    # prompt for eog_user
    # prompt for eog_password # password
    # prompt for country
    # prompt for rollout_date
    questions = config.get('questions-part1')
    # override defaults 
    rollout_date_question = next((q for q in questions if q["name"] == "rollout_date"), None)
    if rollout_date_question:
        rollout_date_question["default"] = datetime.now().strftime("%Y-%m-%d")

    print_json(dict(questions=questions))    
    answers = prompt(questions, answers=orig_answers)
    print_json(dict(answers=answers))

    defaults = filter(lambda x: x["name"] == country_name, config.get(notebook_type,[]))
    defaults = list(defaults)
    if defaults:
        default_config = defaults[0]
        country_code = default_config.get("code","")
        country_osm = default_config.get("country_osm","")
        model_gdrive_url = default_config.get("model_weights_url")
        dhs_dta_prefix = default_config.get("dhs_stata_prefix","")
        dhs_geo_prefix = default_config.get("dhs_geo_prefix","")
    
    # prompt for country-code, country-osm, model-gdrive-url, dhs-dta-prefix, dhs-geo-prefix
    task_type = "rollout"

    # depending on task type
    eog_user_id = "eog_user_id"
    eog_password = "eog_password"
    ookla_year = "2019"
    nightlights_year = "2016"

    os.environ['EOG_USER'] = eog_user_id
    os.environ['EOG_PASSWORD'] = eog_password
    task_stages = dict(
        rollout=["2_generate_grids", "3_rollout_model"],
        train=["0_generate_training_data", "1_train_model"],
        all=["0_generate_training_data", "1_train_model", "2_generate_grids", "3_rollout_model"]
    )
    stage_params = {
        "0_generate_training_data": dict(
                                        COUNTRY_CODE=country_code,
                                        COUNTRY_OSM=country_osm,
                                        ROLLOUT_DATE=rollout_date,
                                        DHS_DTA_PREFIX=dhs_dta_prefix,
                                        DHS_GEO_PREFIX=dhs_geo_prefix,

                                        ),
        "1_train_model": dict(
                                COUNTRY_CODE=country_code,  
                                ROLLOUT_DATE=rollout_date,
                                COUNTRY_OSM=country_osm,
                                OOKLA_YEAR=ookla_year,
                                NIGHTLIGHTS_YEAR=nightlights_year,
                            ),
        "2_generate_grids": dict(
                                COUNTRY_CODE=country_code, 
                                ROLLOUT_DATE=rollout_date,
                                ),
        "3_rollout_model": dict(COUNTRY_CODE=country_code, 
                                ROLLOUT_DATE=rollout_date,
                                COUNTRY_OSM=country_osm,
                                OOKLA_YEAR=ookla_year,
                                NIGHTLIGHTS_YEAR=nightlights_year,
                                # model_gdrive_url is None for task_type == "all"
                                MODEL_GDRIVE_URL=model_gdrive_url if task_type == "rollout" else None 
                                )
    }
    # get parameters
    stages = task_stages.get(task_type, [])

    input_notebook_dir = f"notebooks/{notebook_type}"

    output_notebook_dir = f"output-notebooks/{notebook_type}"
    
    # execute
    for stage in stages:
        output_stage = f"{country_code}_{stage}"
        exec_pm(
            f"{input_notebook_dir}/{stage}.ipynb",
            f"{output_notebook_dir}/{output_stage}.ipynb",
            parameters=stage_params[stage],
            debug=DEBUG
        )


if __name__ == "__main__":
    main()
