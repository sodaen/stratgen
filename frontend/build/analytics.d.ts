export type AnalyticsMeta = Record<string, any>;
export interface AnalyticsOptions {
    projectId?: string | null;
    userId?: string | null;
}
export declare function logAnalytics(event: string, meta?: AnalyticsMeta, opts?: AnalyticsOptions): Promise<boolean>;
export default logAnalytics;
//# sourceMappingURL=analytics.d.ts.map