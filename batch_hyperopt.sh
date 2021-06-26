#!/bin/bash
echo Current Date and Time is: `date +"%Y-%m-%d %T"` >>user_data/batch/CMCWinner_btc50.txt
freqtrade hyperopt --config user_data/config/config_BTC50.json --hyperopt-loss SharpeHyperOptLossDaily  --strategy  CMCWinner --spaces all -e 1000 >>user_data/batch/CMCWinner_btc50.txt
echo Current Date and Time is: `date +"%Y-%m-%d %T"` >>user_data/batch/CMCWinner_USDT50.txt
freqtrade hyperopt --config user_data/config/config_USDT50.json --hyperopt-loss SharpeHyperOptLossDaily  --strategy  CMCWinner --spaces all -e 1000 >>user_data/batch/CMCWinner_USDT50.txt
echo Current Date and Time is: `date +"%Y-%m-%d %T"` >>user_data/batch/BinHV45_USDT50.txt
freqtrade hyperopt --config user_data/config/config_USDT50.json --hyperopt-loss SharpeHyperOptLossDaily  --strategy  BinHV45 --spaces buy -e 1000 >>user_data/batch/BinHV45_USDT50.txt
echo Current Date and Time is: `date +"%Y-%m-%d %T"` >>user_data/batch/BinHV45_BTC50.txt
freqtrade hyperopt --config user_data/config/config_BTC50.json --hyperopt-loss SharpeHyperOptLossDaily  --strategy  BinHV45 --spaces buy -e 1000 >>user_data/batch/BinHV45_BTC50.txt
