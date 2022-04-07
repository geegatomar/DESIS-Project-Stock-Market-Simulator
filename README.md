# DESIS Ascend Educare: Stock Market Project

### Steps to run locally

1. Fork the project, and clone locally
2. Use a virtual environment, and then install all dependencies using 'requirements.txt' file provided.
3. Create the database by doing the 'migrate' in django:
4. 			python3 manage.py migrate
5. Make sure you populate the db with fixtures before running the app. To initialize all fixtures, run the following commands:
6. 			python3 manage.py loaddata bots_data
7. 			python3 manage.py loaddata stock_data
8. 			python3 manage.py loaddata bot_shares_data
9. Finally, run the project using the following command:
10. 		python3 manage.py runserver
11. Check the Makefile for common commands, and you can directly execute them also.


### Project Explanation
- TODO: Add explanation
- TODO: Add database diagrams, and all other workflow diagrams here
- TODO: Explain all the functionalities, and additional functionalities such as the rate limiter we added
- TODO: Explain our main order matching algorithm, and why we took 4 queues

- TODO: Also add a future work and caveats section


### Team
#### Members:
- Shivangi Tomar
- Jyotsana Srivastava                                                             
- Radhika Gupta
- Mansi Agarwal
- Anshika Yadav

#### Mentors:
- Ashutosh Bang
- Pratyush Kamal Chaudhary
