"""
Options Day-Trading Assistant
A personal trading tool for identifying high-probability options trades.

Main entry point for the trading system.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import load_settings
from src.utils.logger import setup_logger, get_logger
from src.data import get_client, get_cache
from src.scanner import MarketScanner, OptionsFilter, get_default_symbols
from src.strategies import StrategySelector
from src.analytics import ProbabilityCalculator, RiskMetrics
from src.scoring import TradeScorer
from src.integration import TOSAlertGenerator, WatchlistGenerator


# Initialize
console = Console()
logger = setup_logger()


class TradingSystem:
    """Main trading system orchestrator."""
    
    def __init__(self):
        """Initialize trading system."""
        self.settings = load_settings()
        self.client = get_client()
        self.cache = get_cache()
        
        self.scanner = MarketScanner()
        self.options_filter = OptionsFilter()
        self.strategy_selector = StrategySelector()
        self.scorer = TradeScorer()
    
    def run(self, symbols: List[str] = None):
        """
        Run the complete trading system pipeline.
        
        Args:
            symbols: List of symbols to scan (uses defaults if None)
        """
        console.print(Panel.fit(
            "[bold cyan]Options Day-Trading Assistant[/bold cyan]\n"
            f"[dim]Version 1.0.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
            border_style="cyan"
        ))
        
        # Check if market is open
        if not self.client.is_market_open():
            console.print("[yellow]⚠️  Market is currently closed[/yellow]")
            console.print("[dim]Running in demo mode with cached data...[/dim]\n")
        
        # Use default symbols if none provided
        if symbols is None:
            symbols = get_default_symbols()
            console.print(f"[dim]Scanning {len(symbols)} default symbols[/dim]\n")
        
        all_trades = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Step 1: Market Scanner
            task1 = progress.add_task("[cyan]Scanning market...", total=None)
            candidates = self.scanner.scan_market(symbols)
            progress.update(task1, completed=True)
            console.print(f"✓ Found {len(candidates)} stock candidates\n")
            
            if not candidates:
                console.print("[yellow]No candidates found. Try adjusting filters or scanning more symbols.[/yellow]")
                return
            
            # Step 2: Options Filter & Strategy Selection
            task2 = progress.add_task("[cyan]Analyzing options...", total=len(candidates))
            
            for candidate in candidates:
                symbol = candidate['symbol']
                
                # Filter options
                options_data = self.options_filter.filter_options(symbol)
                if not options_data:
                    progress.advance(task2)
                    continue
                
                # Select strategy
                trade = self.strategy_selector.select_strategy(candidate, options_data)
                if not trade:
                    progress.advance(task2)
                    continue
                
                # Calculate probabilities
                prob_metrics = self._calculate_probabilities(trade)
                
                # Calculate risk metrics
                risk_metrics = RiskMetrics.calculate_trade_metrics(trade)
                
                # Calculate expected value
                if prob_metrics and risk_metrics:
                    ev = RiskMetrics.calculate_expected_value(
                        prob_metrics.get('probability_itm', 0),
                        risk_metrics.get('max_gain', 0),
                        risk_metrics.get('max_loss', 0)
                    )
                    risk_metrics['expected_value'] = ev
                
                # Score trade
                score = self.scorer.score_trade(trade, prob_metrics, risk_metrics, options_data)
                
                # Add to trade
                trade['score'] = score
                trade['probability_metrics'] = prob_metrics
                trade['risk_metrics'] = risk_metrics
                
                all_trades.append(trade)
                progress.advance(task2)
            
            progress.update(task2, completed=True)
        
        console.print(f"✓ Analyzed {len(all_trades)} potential trades\n")
        
        if not all_trades:
            console.print("[yellow]No viable trades found. Market conditions may not be favorable.[/yellow]")
            return
        
        # Step 3: Rank and filter trades
        top_trades = self.scorer.rank_trades(all_trades)
        
        if not top_trades:
            console.print(f"[yellow]No trades scored above {self.settings.min_trade_score}. "
                        f"Consider lowering the threshold.[/yellow]")
            return
        
        # Step 4: Display results
        self._display_trades(top_trades)
        
        # Step 5: Generate outputs
        self._generate_outputs(top_trades)
        
        console.print("\n[bold green]✓ Scan complete![/bold green]")
    
    def _calculate_probabilities(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate probability metrics for a trade."""
        underlying_price = trade.get('underlying_price', 0)
        legs = trade.get('legs', [])
        dte = trade.get('dte', 0)
        
        if not legs or dte <= 0:
            return {}
        
        # Get first leg for calculations
        leg = legs[0]
        strike = leg.get('strike', 0)
        option_type = leg.get('option_type', 'CALL')
        
        # Estimate IV from leg (simplified)
        # In production, extract from actual option data
        iv = 0.30  # 30% default IV
        r = 0.05  # 5% risk-free rate
        T = dte / 365.0
        
        # Calculate probabilities
        prob_metrics = ProbabilityCalculator.calculate_probabilities(
            S=underlying_price,
            K=strike,
            T=T,
            r=r,
            sigma=iv,
            option_type=option_type.lower(),
            run_monte_carlo=True
        )
        
        return prob_metrics
    
    def _display_trades(self, trades: List[Dict[str, Any]]):
        """Display trades in a formatted table."""
        table = Table(title="🎯 Top Trade Opportunities", title_style="bold cyan")
        
        table.add_column("Symbol", style="cyan", no_wrap=True)
        table.add_column("Strategy", style="yellow")
        table.add_column("Bias", style="magenta")
        table.add_column("Strikes", style="white")
        table.add_column("DTE", justify="right", style="blue")
        table.add_column("Max Loss", justify="right", style="red")
        table.add_column("Max Gain", justify="right", style="green")
        table.add_column("R/R", justify="right", style="cyan")
        table.add_column("Score", justify="right", style="bold green")
        
        for trade in trades:
            symbol = trade.get('symbol', '')
            strategy = trade.get('strategy', '')
            bias = trade.get('bias', '').capitalize()
            dte = trade.get('dte', 0)
            score = trade.get('score', 0)
            
            risk_metrics = trade.get('risk_metrics', {})
            max_loss = risk_metrics.get('max_loss', 0)
            max_gain = risk_metrics.get('max_gain', 0)
            rr_ratio = risk_metrics.get('risk_reward_ratio', 0)
            
            # Get strikes
            legs = trade.get('legs', [])
            strikes = ' / '.join([f"{leg.get('strike', 0):.0f}" for leg in legs])
            
            table.add_row(
                symbol,
                strategy,
                bias,
                strikes,
                str(dte),
                f"${max_loss:.0f}",
                f"${max_gain:.0f}" if max_gain != float('inf') else "Unlimited",
                f"{rr_ratio:.2f}",
                f"{score:.0f}"
            )
        
        console.print(table)
        
        # Print detailed explanations
        console.print("\n[bold]Trade Explanations:[/bold]\n")
        for i, trade in enumerate(trades, 1):
            symbol = trade.get('symbol')
            explanation = trade.get('explanation', 'No explanation available')
            console.print(f"[cyan]{i}. {symbol}:[/cyan] {explanation}")
    
    def _generate_outputs(self, trades: List[Dict[str, Any]]):
        """Generate output files for trades."""
        console.print("\n[bold]Generating outputs...[/bold]")
        
        # Save trades to JSON
        output_dir = Path("outputs/trades")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y-%m-%d')
        json_file = output_dir / f"trades_{timestamp}.json"
        
        with open(json_file, 'w') as f:
            json.dump(trades, f, indent=2, default=str)
        
        console.print(f"✓ Saved trades: {json_file}")
        
        # Generate ThinkScript alerts
        risk_metrics_list = [t.get('risk_metrics', {}) for t in trades]
        alert_files = TOSAlertGenerator.generate_batch_alerts(trades, risk_metrics_list)
        console.print(f"✓ Generated {len(alert_files)} ThinkScript alerts")
        
        # Generate watchlists
        watchlist_file = WatchlistGenerator.generate_watchlist(trades)
        console.print(f"✓ Generated watchlist: {watchlist_file}")
        
        detailed_watchlist = WatchlistGenerator.generate_detailed_watchlist(trades, risk_metrics_list)
        console.print(f"✓ Generated detailed watchlist: {detailed_watchlist}")
        
        # Save scan results to cache
        self.cache.save_scan_results(trades)


def main():
    """Main entry point."""
    try:
        system = TradingSystem()
        system.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Scan interrupted by user[/yellow]")
    except Exception as e:
        logger.error(f"System error: {e}", exc_info=True)
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        console.print("[dim]Check logs/trading_system_*.log for details[/dim]")


if __name__ == "__main__":
    main()
