const bitprophet = require('bitprophet')
bitprophet.options({
    binance: {
        key: y4DKZ3JcP8RuiAPiwSase6UiV5gRF64grVRrCAWbibQ1ihUoGQiBCssVCd4RWbX1,
        secret: v8nQKE5WDjkgasDmRCUdj60QyfSGmS4JmvRi8LcO0MgUTQjWpdfhFDJoAFG6Xf6k
    },
    telegram: {
        chatId: -1583337118,
        token: 1079258072:AAHkQCLoM2d0lMPhRZeSJi1cFsNtWxttKdk
    }
})

bitprophet.start()
