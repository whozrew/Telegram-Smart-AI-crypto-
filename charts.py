import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import io

def generate_professional_chart(df: pd.DataFrame, coin: str, signal_data: dict) -> io.BytesIO:
    """Spot savdo zonalari aks etgan to'q rangli professional grafik generatori"""
    # Oxirgi 60 ta shamni olish
    df_plot = df.tail(60).copy()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    fig.patch.set_facecolor('#121212')
    ax1.set_facecolor('#121212')
    ax2.set_facecolor('#121212')

    # Shamdonlar (Candlesticks) chizish logikasi
    for idx, row in df_plot.iterrows():
        color = '#00c853' if row['close'] >= row['open'] else '#ff3d00'
        # Wick
        ax1.plot([idx, idx], [row['low'], row['high']], color=color, linewidth=1.5)
        # Body
        ax1.plot([idx, idx], [row['open'], row['close']], color=color, linewidth=6, solid_capstyle='round')

    # Indikatorlar chizish
    if 'EMA20' in df_plot.columns:
        ax1.plot(df_plot.index, df_plot['EMA20'], color='#2196f3', label='EMA 20', linewidth=1)
    if 'EMA50' in df_plot.columns:
        ax1.plot(df_plot.index, df_plot['EMA50'], color='#ff9800', label='EMA 50', linewidth=1)
    if 'EMA200' in df_plot.columns:
        ax1.plot(df_plot.index, df_plot['EMA200'], color='#e91e63', label='EMA 200', linewidth=1.5)

    # Savdo darajalarini gorizontal chiziqlar bilan chizish (Faqat sotib olish signallari uchun)
    if "SOTIB OLISH" in signal_data["signal"]:
        last_idx = df_plot.index[-1]
        ax1.axhline(signal_data["price"], color='#00e676', linestyle='--', alpha=0.8, label=f"Kirish: {signal_data['price']}")
        ax1.axhline(signal_data["stop_loss"], color='#ff1744', linestyle='--', alpha=0.8, label=f"SL: {signal_data['stop_loss']}")
        ax1.axhline(signal_data["tp1"], color='#00b0ff', linestyle=':', alpha=0.7, label=f"TP1: {signal_data['tp1']}")
        ax1.axhline(signal_data["tp3"], color='#d500f9', linestyle=':', alpha=0.7, label=f"TP3: {signal_data['tp3']}")
        
        # Risk zonalari vizual rangli to'rtburchak
        ax1.axhspan(signal_data["stop_loss"], signal_data["price"], color='#ff1744', alpha=0.05)
        ax1.axhspan(signal_data["price"], signal_data["tp3"], color='#00e676', alpha=0.05)

    ax1.set_title(f"{coin} - Halol Spot Tahlili ({signal_data['signal']})", color='white', fontsize=14, fontweight='bold')
    ax1.tick_params(colors='white')
    ax1.grid(color='#262626', linestyle='-', linewidth=0.5)
    ax1.legend(loc='upper left', facecolor='#1e1e1e', edgecolor='#262626', labelcolor='white')

    # Hajm (Volume Panel)
    colors_vol = ['#00c853' if c >= o else '#ff3d00' for c, o in zip(df_plot['close'], df_plot['open'])]
    ax2.bar(df_plot.index, df_plot['volume'], color=colors_vol, alpha=0.7)
    ax2.tick_params(colors='white')
    ax2.grid(color='#262626', linestyle='-', linewidth=0.5)
    ax2.set_ylabel('Hajm', color='white')

    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none')
    buf.seek(0)
    plt.close(fig)
    return buf
