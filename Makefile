# Makefile for project setup
.PHONY: build run stop

build:
	docker-compose build
run:
	docker-compose up
stop:
	docker-compose down

