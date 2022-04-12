# DESIS Ascend Educare: Stock Market Project

[Project Report](https://docs.google.com/document/d/1RiM_tJUNKYW4TEI1FXe0eJpksxBhiu2sgpSmr4f03NQ/edit?usp=sharing)

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
