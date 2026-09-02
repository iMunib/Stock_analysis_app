import React from "react";

/** Never render a blank screen: catch render errors and offer a reload. */
export class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="mx-auto max-w-desk px-6 py-16" role="alert">
          <div className="rounded-md border border-bad/50 bg-bad/10 px-6 py-6">
            <h1 className="font-display text-2xl text-paper">Something went wrong</h1>
            <p className="mt-2 text-sm text-fog">{this.state.error.message}</p>
            <button
              onClick={() => this.setState({ error: null })}
              className="mt-4 rounded border border-line px-4 py-2 text-sm text-paper hover:border-gold"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
