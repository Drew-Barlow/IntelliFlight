from .models.bayes_net import Bayes_Net

x = Bayes_Net()
x.train_model('data/historical/flights/T_ONTIME_MARKETING.csv', 10, .02, .1)
