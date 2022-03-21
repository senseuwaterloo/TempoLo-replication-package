# On the Temporal Relations between Logging and Code

This repo contains the data and the source code of  the tool (i.e., **TempoLo**) used in our paper *On the Temporal Relations between Logging and Code*. 

The `data` folder contains the data files used in our paper and the jupyter contains the jupyter notebooks for reproducing the results. Two files `tempolo_semantic.py` and `inconsistency_detection.py` are the two source files that implemented the rules and findings from our paper. The file `config.json` is used for keeping the info of the database connections.

## Requirements and Installation

* Python version == 3.6
* Postgresql
* srcML
* Refer to `spec-file.txt` for the dependent library


## Data description

The data can be found in the `data` directory, which contains six files: 

* `all_local_string.pkl`: the file cotnains all the extracted local strings from Tomcat project, which is used dring the extraction of the logging text. 
* `sampled_logs.csv`: the file contains the sampled log statements extract from four projects.
* `ground_truth.csv`: the file contains the manually identified temporal inconsistencies from the sampled data, which is used as our first evaluation data
* `detected-log-code-inconsistency.csv`: the file contains the detected temporal inconsistencies from the remaining data, which is used as our second evaluation data
* `commit-history.csv`: the file contains the temporal inconsistencies mined from commit history, which is used as our third evaluation data.
* `tempolo.sql.zip`: the file is split into two parts and contains all the extracted logging statements as well as the methods from the four projects.

## Replicate the results
> 1. Create a database named **logs** using the PostgreSQL.

> 2. Unzip the file **tempolo.sql.zip**, and restore it to the DB: logs using command **pg_restore**.

> 3. Modify the configuration file: **config.json** with your own database information.

> 4. Change the directory to the **jupyter**, and run the following command:
```
jupyter notebook
```

> 5. The notebook file **Replication-Package.ipynb** contains all the source code for reproducing the results reported in our paper.


