<p align="center">
  <img src="/gif/sanic.gif"/>
</p>

<h1 align="center"> 🐍 Rinha de Backend 🐍 </h1>

This project was produced for a participation in a community driven challenge that can be found <a href="https://github.com/zanfranceschi/rinha-de-backend-2023-q3">here</a>.   
The main challenge idea is not the api itself, but the optimization to handle a stress test close to a ddos, using only 1.5 vCPU and 3GB of RAM.   
This version does not attempt to be a production like code and does not apply much of good design standards, everything like that are a completely overengineering to the challenge propose.   
The main features applied to increase performance was:   

- asynchronous everywhere due to the i/o bound characteristics of the challenge.
- background task queue and bulk insert to creation endpoint.   
- cache for people queries.   
- searcheable generated column and trigram index for 'like' query.   
- unix socket connection between nginx and api's nodes.   

it reached 21' position at challenge and 1' made in python.   

Stack:   
- Python
- Sanic
- PostgreSQL
- Redis
- Nginx

results can be found here:   
https://iancambrea.github.io/rinha-python-sanic/rinhabackendsimulation-20230823140802726/
