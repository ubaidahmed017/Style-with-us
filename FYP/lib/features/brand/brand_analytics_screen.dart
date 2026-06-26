import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../core/theme.dart';

class BrandAnalyticsScreen extends ConsumerStatefulWidget {
  const BrandAnalyticsScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<BrandAnalyticsScreen> createState() => _BrandAnalyticsScreenState();
}

class _BrandAnalyticsScreenState extends ConsumerState<BrandAnalyticsScreen> {
  String _timeRange = '7 Days';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Brand Analytics'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/brand'),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12.0),
            child: DropdownButton<String>(
              value: _timeRange,
              underline: const SizedBox(),
              items: ['7 Days', '30 Days', '12 Months']
                  .map((range) => DropdownMenuItem(
                        value: range,
                        child: Text(range),
                      ))
                  .toList(),
              onChanged: (val) {
                if (val != null) {
                  setState(() => _timeRange = val);
                }
              },
            ),
          )
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Stats grid
            Row(
              children: [
                Expanded(
                  child: _buildMetricCard(
                    context,
                    title: 'Total Revenue',
                    value: '\$4,820.50',
                    subtitle: '+12% from last week',
                    icon: Icons.monetization_on_outlined,
                    iconColor: Colors.green,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildMetricCard(
                    context,
                    title: 'Orders Placed',
                    value: '64',
                    subtitle: '+8% from last week',
                    icon: Icons.shopping_basket_outlined,
                    iconColor: Colors.blue,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _buildMetricCard(
                    context,
                    title: 'Items Sold',
                    value: '112',
                    subtitle: 'Avg. 1.7 items/order',
                    icon: Icons.checkroom_outlined,
                    iconColor: Colors.purple,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildMetricCard(
                    context,
                    title: 'Conversion Rate',
                    value: '3.4%',
                    subtitle: '+0.5% vs last month',
                    icon: Icons.trending_up,
                    iconColor: Colors.amber,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Revenue Line Chart Card
            _buildChartCard(
              context,
              title: 'Revenue Trend (\$)',
              subtitle: 'Daily earnings over the selected period',
              chart: SizedBox(
                height: 200,
                child: LineChart(
                  _getRevenueChartData(),
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Category Sales Breakdown Card
            _buildChartCard(
              context,
              title: 'Sales by Gender Target',
              subtitle: 'Distribution of sold items',
              chart: SizedBox(
                height: 180,
                child: Row(
                  children: [
                    Expanded(
                      flex: 4,
                      child: PieChart(
                        _getCategoryChartData(),
                      ),
                    ),
                    Expanded(
                      flex: 3,
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildLegendItem('Men (Male)', Colors.blue, '45%'),
                          const SizedBox(height: 8),
                          _buildLegendItem('Women (Female)', Colors.pinkAccent, '35%'),
                          const SizedBox(height: 8),
                          _buildLegendItem('Unisex', Colors.purple, '20%'),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricCard(
    BuildContext context, {
    required String title,
    required String value,
    required String subtitle,
    required IconData icon,
    required Color iconColor,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Icon(icon, color: iconColor, size: 20),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              value,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              subtitle,
              style: TextStyle(
                fontSize: 10,
                color: subtitle.contains('+') ? AppColors.success : AppColors.textMuted,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChartCard(
    BuildContext context, {
    required String title,
    required String subtitle,
    required Widget chart,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            Text(
              subtitle,
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 24),
            chart,
          ],
        ),
      ),
    );
  }

  Widget _buildLegendItem(String label, Color color, String percentage) {
    return Row(
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            label,
            style: const TextStyle(fontSize: 12, color: AppColors.textPrimary),
          ),
        ),
        Text(
          percentage,
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textSecondary),
        ),
      ],
    );
  }

  LineChartData _getRevenueChartData() {
    return LineChartData(
      gridData: const FlGridData(show: false),
      titlesData: FlTitlesData(
        topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        bottomTitles: AxisTitles(
          sideTitles: SideTitles(
            showTitles: true,
            getTitlesWidget: (value, meta) {
              const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
              if (value.toInt() >= 0 && value.toInt() < days.length) {
                return SideTitleWidget(
                  axisSide: meta.axisSide,
                  child: Text(days[value.toInt()], style: const TextStyle(fontSize: 10, color: AppColors.textMuted)),
                );
              }
              return const SizedBox();
            },
          ),
        ),
      ),
      borderData: FlBorderData(show: false),
      lineBarsData: [
        LineChartBarData(
          spots: const [
            FlSpot(0, 320),
            FlSpot(1, 480),
            FlSpot(2, 410),
            FlSpot(3, 620),
            FlSpot(4, 520),
            FlSpot(5, 780),
            FlSpot(6, 850),
          ],
          isCurved: true,
          color: AppColors.primary,
          barWidth: 4,
          isStrokeCapRound: true,
          dotData: const FlDotData(show: true),
          belowBarData: BarAreaData(
            show: true,
            color: AppColors.primary.withOpacity(0.15),
          ),
        ),
      ],
    );
  }

  PieChartData _getCategoryChartData() {
    return PieChartData(
      sectionsSpace: 4,
      centerSpaceRadius: 30,
      sections: [
        PieChartSectionData(
          color: Colors.blue,
          value: 45,
          title: '45%',
          radius: 40,
          titleStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white),
        ),
        PieChartSectionData(
          color: Colors.pinkAccent,
          value: 35,
          title: '35%',
          radius: 40,
          titleStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white),
        ),
        PieChartSectionData(
          color: Colors.purple,
          value: 20,
          title: '20%',
          radius: 40,
          titleStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white),
        ),
      ],
    );
  }
}
