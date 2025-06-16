# DataHat

####  ETL For Upstox and Dhan NSE Equity

#### Steps to run the code

* Create the virtual environment 
* Activate the virtual environment
* Install the packages using `requirements.txt` file
* Edit the `.env` file for the urls, files, Database config settings , filters 
* Change the values for the connection settings for the Mongo and SQLITE if you want to run in your machine
* If you are using please pull docker for MongoDB
* Give the output_path and log_path for the log files  and output files to read .
* Once every thing is done as per your setting run `python main.py`

### Steps to install MongoDB using Docker

* Install docker desktop in Mac or Windows
* Login to the docker hub with respective crendentials
* Once login, search in the docker hub for mongoDB `mongodb/mongodb-community-server:6.0.13-ubuntu2204` .
* Do docker pull to install the image.
* Run the container from the docker.
* Check the port where the MongoDB is running from the container page and use the same in the `.env`  file

