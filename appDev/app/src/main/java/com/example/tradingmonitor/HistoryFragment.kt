package com.example.tradingmonitor

import android.graphics.Color
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.github.mikephil.charting.charts.LineChart
import com.github.mikephil.charting.components.XAxis
import com.github.mikephil.charting.components.YAxis
import com.github.mikephil.charting.data.Entry
import com.github.mikephil.charting.data.LineData
import com.github.mikephil.charting.data.LineDataSet
import com.github.mikephil.charting.formatter.IndexAxisValueFormatter
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class HistoryFragment : Fragment() {

    private lateinit var lineChart: LineChart

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_history, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        lineChart = view.findViewById(R.id.lineChart)
        
        loadHistory()
    }

    private fun loadHistory() {
        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val historyList = withContext(Dispatchers.IO) {
                    RetrofitClient.historyApi.getHistory()
                }

                if (historyList.isNotEmpty()) {
                    setupChart(historyList)
                } else {
                    Toast.makeText(context, "저장된 히스토리가 없습니다.", Toast.LENGTH_SHORT).show()
                }

            } catch (e: Exception) {
                e.printStackTrace()
                Toast.makeText(context, "서버 연결 실패: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun setupChart(historyList: List<HistoryItem>) {
        lineChart.description.isEnabled = false
        lineChart.setTouchEnabled(true)
        lineChart.isDragEnabled = true
        lineChart.setScaleEnabled(true)
        lineChart.setPinchZoom(true)

        // X-Axis (Dates)
        val xAxis = lineChart.xAxis
        xAxis.position = XAxis.XAxisPosition.BOTTOM
        xAxis.setDrawGridLines(false)
        xAxis.valueFormatter = IndexAxisValueFormatter(historyList.map { it.date.substring(5) }) // MM-dd
        xAxis.granularity = 1f

        // Left Axis (Score: 0-100)
        val leftAxis = lineChart.axisLeft
        leftAxis.setDrawGridLines(true)
        leftAxis.axisMinimum = 0f
        leftAxis.axisMaximum = 100f
        leftAxis.textColor = Color.BLUE

        // Right Axis (BTC Price)
        val rightAxis = lineChart.axisRight
        rightAxis.isEnabled = true
        rightAxis.setDrawGridLines(false)
        rightAxis.textColor = Color.RED

        // Data Entries
        val scoreEntries = ArrayList<Entry>()
        val priceEntries = ArrayList<Entry>()



        // Score DataSet
        val scoreDataSet = LineDataSet(scoreEntries, "투자 점수")
        scoreDataSet.axisDependency = YAxis.AxisDependency.LEFT
        scoreDataSet.color = Color.BLUE
        scoreDataSet.setCircleColor(Color.BLUE)
        scoreDataSet.lineWidth = 2f
        scoreDataSet.circleRadius = 4f
        scoreDataSet.valueTextSize = 10f

        // Price DataSet
        val priceDataSet = LineDataSet(priceEntries, "BTC 가격")
        priceDataSet.axisDependency = YAxis.AxisDependency.RIGHT
        priceDataSet.color = Color.RED
        priceDataSet.setCircleColor(Color.RED)
        priceDataSet.lineWidth = 2f
        priceDataSet.circleRadius = 0f // Hide circles for price to avoid clutter
        priceDataSet.setDrawValues(false)

        val lineData = LineData(scoreDataSet, priceDataSet)
        lineChart.data = lineData
        lineChart.invalidate() // Refresh
    }
}
