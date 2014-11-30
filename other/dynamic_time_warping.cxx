/*
FROM WIKIPEDIA:

note d(...) is a distance metric, maybe abs(s[i] - t[j])

int DTWDistance(s: array [1..n], t: array [1..m], w: int) {
    DTW := array [0..n, 0..m]
 
    w := max(w, abs(n-m)) // adapt window size (*)
 
    for i := 0 to n
        for j:= 0 to m
            DTW[i, j] := infinity
    DTW[0, 0] := 0

    for i := 1 to n
        for j := max(1, i-w) to min(m, i+w)
            cost := d(s[i], t[j])
            DTW[i, j] := cost + minimum(DTW[i-1, j  ],    // insertion
                                        DTW[i, j-1],    // deletion
                                        DTW[i-1, j-1])    // match
 
    return DTW[n, m]
*/

#include <cmath>

int min3(int n1, int n2, int n3) {
    if (n1 < n2 && n1 < n3) {
        return n1;
    } else if (n2 < n1 && n2 < n3) {
        return n2;
    } else {
        return n3;
    }
}

int dtw_distance(int *s1, int s1_length, int *s2, int s2_length, int w) {
    int **dtw = new int*[s1_length + 1];
    for (int i = 0; i < s1_length + 1; i++) {
        dtw[i] = new int[s2_length + 1];
        for (int j = 0; j < s2_length + 1; j++) dtw[i][j] = 10000;  //infinity
    }
    dtw[0][0] = 0;

    w = fmax(w, fabs(s1_length - s2_length));

    for (int i = 1; i < s1_length + 1; i++) {
        for (int j = fmax(1, i - w); j < fmin(s2_length + 1, i + w); j++) {
            dtw[i][j] = fabs(s1[i] - s2[j]) +
                        min3( dtw[i - 1][j    ],
                              dtw[i    ][j - 1],
                              dtw[i - 1][j - 1] );
        }
    }

    int cost = dtw[s1_length][s2_length];

    for (int i = 0; i < s1_length; i++) {
        delete[] dtw[i];
    }
    delete[] dtw;


    return cost;
}

