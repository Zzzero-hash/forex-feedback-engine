class FeedbackLoop:
    def __init__(self, database_url=None):
        # Optional database URL for logging or persistence
        self.database_url = database_url
        self.trade_history = []
        # Setup database connection if provided
        if database_url:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from .models import Base, Trade

            self.engine = create_engine(database_url)
            Base.metadata.create_all(self.engine)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
        else:
            self.session = None

        self.performance_metrics = {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0
        }
        self.strategy_adjusted = False

    def record_trade(self, decision, outcome):
        self.trade_history.append({'decision': decision, 'outcome': outcome})
        self.performance_metrics['total_trades'] += 1
        if outcome == 'win':
            self.performance_metrics['wins'] += 1
        else:
            self.performance_metrics['losses'] += 1
        self.update_win_rate()

    def record_trade_outcome(self, decision, outcome):
        """Record a trade outcome where outcome is a boolean indicating win (True) or loss (False)."""
        # Append to history as boolean
        self.trade_history.append({'decision': decision, 'outcome': outcome})
        # Update performance metrics
        self.performance_metrics['total_trades'] += 1
        if outcome:
            self.performance_metrics['wins'] += 1
        else:
            self.performance_metrics['losses'] += 1
        self.update_win_rate()
        # Persist trade to database if session available
        if self.session:
            from .models import Trade
            trade = Trade(decision=decision, outcome=outcome)
            self.session.add(trade)
            self.session.commit()

    def calculate_win_rate(self):
        """Return the current win rate."""
        return self.performance_metrics.get('win_rate', 0.0)

    def update_win_rate(self):
        if self.performance_metrics['total_trades'] > 0:
            self.performance_metrics['win_rate'] = (
                self.performance_metrics['wins'] / self.performance_metrics['total_trades']
            )

    def get_performance_metrics(self):
        return self.performance_metrics

    def analyze_trade_history(self):
        # Placeholder for future analysis logic
        pass

    def adjust_strategy(self):
        # Simple flag to indicate strategy was adjusted
        self.strategy_adjusted = True

    def should_end_session(self, initial_balance: float, trade_amount: float,
                           profit_target_pct: float, loss_limit_pct: float) -> bool:
        """
        Determine if session should end based on PnL reaching profit target or loss limit.
        PnL percent = (wins - losses) * trade_amount / initial_balance * 100
        """
        wins = self.performance_metrics.get('wins', 0)
        losses = self.performance_metrics.get('losses', 0)
        pnl = (wins - losses) * trade_amount
        pnl_pct = (pnl / initial_balance) * 100 if initial_balance else 0.0
        if pnl_pct >= profit_target_pct or pnl_pct <= -loss_limit_pct:
            return True
        return False