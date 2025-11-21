package com.example.tradingmonitor

import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class HomeFragment : Fragment() {

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_home, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        setupClickListeners(view)
        fetchData(view)
    }

    private fun setupClickListeners(view: View) {
        view.findViewById<View>(R.id.cardFearGreed).setOnClickListener {
            openUrl("https://alternative.me/crypto/fear-and-greed-index/")
        }
        view.findViewById<View>(R.id.cardRsi).setOnClickListener {
            openUrl("https://www.binance.com/en/trade/BTC_USDT")
        }
        view.findViewById<View>(R.id.cardCbPremium).setOnClickListener {
            openUrl("https://cryptoquant.com/asset/btc/chart/market-indicator/coinbase-premium-index")
        }
        view.findViewById<View>(R.id.cardGoogleTrends).setOnClickListener {
            openUrl("https://trends.google.com/trends/explore?q=Bitcoin")
        }
        view.findViewById<View>(R.id.btnRefresh).setOnClickListener {
            fetchData(view)
        }
    }

    private fun fetchData(view: View) {
        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val btnRefresh = view.findViewById<Button>(R.id.btnRefresh)
                btnRefresh.isEnabled = false
                btnRefresh.text = "데이터 불러오는 중..."

                // Fetch from Python Server
                val historyList = withContext(Dispatchers.IO) {
                    RetrofitClient.historyApi.getHistory()
                }

                if (historyList.isNotEmpty()) {
                    val latest = historyList.last()
                    updateUI(view, latest)
                } else {
                    Toast.makeText(context, "데이터가 없습니다. 서버를 확인하세요.", Toast.LENGTH_SHORT).show()
                }

            } catch (e: Exception) {
                e.printStackTrace()
                Toast.makeText(context, "Error: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                val btnRefresh = view.findViewById<Button>(R.id.btnRefresh)
                btnRefresh.isEnabled = true
                btnRefresh.text = "새로고침 (데이터 갱신)"
            }
        }
    }

    private fun updateUI(view: View, data: HistoryItem) {
        // Total Score
        view.findViewById<TextView>(R.id.txtTotalScore).text = "${data.total_score}점"
        
        // 1. Fear & Greed
        view.findViewById<TextView>(R.id.txtFearGreed).text = "${data.fear_greed}"
        
        // 2. RSI
        view.findViewById<TextView>(R.id.txtRsi).text = String.format("%.1f", data.rsi)
        
        // 3. Coinbase Premium
        view.findViewById<TextView>(R.id.txtCbPremium).text = String.format("%.3f%%", data.coinbase_premium)
        
        // 4. Google Trends
        view.findViewById<TextView>(R.id.txtGoogleTrends).text = "${data.google_trends}"
        
        // Update Status Text based on Total Score
        val txtStatus = view.findViewById<TextView>(R.id.txtStatus)
        when {
            data.total_score >= 80 -> {
                txtStatus.text = "강력 매수 (Strong Buy)"
                txtStatus.setTextColor(Color.RED)
            }
            data.total_score >= 60 -> {
                txtStatus.text = "매수 (Buy)"
                txtStatus.setTextColor(Color.parseColor("#FF5722")) // Orange
            }
            data.total_score <= 20 -> {
                txtStatus.text = "강력 매도 (Strong Sell)"
                txtStatus.setTextColor(Color.BLUE)
            }
            data.total_score <= 40 -> {
                txtStatus.text = "매도 (Sell)"
                txtStatus.setTextColor(Color.parseColor("#2196F3")) // Light Blue
            }
            else -> {
                txtStatus.text = "관망 (Neutral)"
                txtStatus.setTextColor(Color.GRAY)
            }
        }
    }

    private fun openUrl(url: String) {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
        startActivity(intent)
    }
}
