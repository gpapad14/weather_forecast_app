install:
	#install commands
	pip install --upgrade pip &&\
		pip install -r requirements.txt
format:
	#format code
lints:
	#flake8 or #pylint
test:
	#test
deplay:
	#deploy
all: install lint test deploy
