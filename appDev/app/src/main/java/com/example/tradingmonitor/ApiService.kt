package com.example.tradingmonitor

import com.google.gson.annotations.SerializedName
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.GET
import retrofit2.http.Query

// 1. Fear & Greed API
data class FearGreedResponse(
    @SerializedName("data") val data: List<FearGreedData>
)

data class FearGreedData(
    @SerializedName("value") val value: String,
    @SerializedName("value_classification") val classification: String
)

interface FngApi {
    @GET("fng/")
    suspend fun getFearGreed(@Query("limit") limit: Int = 1): FearGreedResponse
}

// 2. Binance API (for RSI calculation)
// Response format: [ [timestamp, open, high, low, close, volume, ...], ... ]
// We only need Close price (index 4)
interface BinanceApi {
    @GET("api/v3/klines")
    suspend fun getKlines(
        @Query("symbol") symbol: String = "BTCUSDT",
        @Query("interval") interval: String = "1d",
        @Query("limit") limit: Int = 100 // Need enough data for RSI
    ): List<List<Any>>
}

// 3. History API (from Python Server)
data class HistoryItem(
    val date: String,
    val timestamp: Long,
    val total_score: Int,
    val fear_greed: Int,
    val coinbase_premium: Double,
    val google_trends: Int,
    val rsi: Double,
    val btc_price: Double
)

interface HistoryApi {
    @GET("history")
    suspend fun getHistory(): List<HistoryItem>
}

// Network Object
object RetrofitClient {
    private const val BASE_URL_FNG = "https://api.alternative.me/"
    private const val BASE_URL_BINANCE = "https://api.binance.com/"
    
    // [중요] 서버 IP 설정
    // 1. 에뮬레이터 사용 시: "http://10.0.2.2:5000/" (PC의 localhost를 가리킴)
    // 2. 실제 폰 사용 시: PC의 내부 IP를 입력해야 함 (예: "http://192.168.0.10:5000/")
    //    - 확인 방법: 윈도우 터미널에서 'ipconfig' 입력 후 'IPv4 주소' 확인
    private const val BASE_URL_SERVER = "http://10.0.2.2:5000/" 

    val fngApi: FngApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL_FNG)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(FngApi::class.java)
    }

    val binanceApi: BinanceApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL_BINANCE)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(BinanceApi::class.java)
    }
    
    val historyApi: HistoryApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL_SERVER)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(HistoryApi::class.java)
    }
}
