# polynomial regression, by ChatGPT

import math

def polynomial_regression(x, y, degree):
    # Create a matrix for Vandermonde-like terms
    def create_vandermonde_matrix(x, degree):
        return [[x_i**d for d in range(degree + 1)] for x_i in x]
    
    # Transpose a matrix
    def transpose(matrix):
        return list(map(list, zip(*matrix)))
    
    # Multiply two matrices
    def matrix_multiply(A, B):
        result = [[sum(a * b for a, b in zip(A_row, B_col)) for B_col in zip(*B)] for A_row in A]
        return result
    
    # Multiply matrix by vector
    def matrix_vector_multiply(matrix, vector):
        return [sum(m * v for m, v in zip(row, vector)) for row in matrix]
    
    # Invert a square matrix using Gaussian elimination
    def invert_matrix(matrix):
        n = len(matrix)
        identity = [[float(i == j) for i in range(n)] for j in range(n)]
        for i in range(n):
            # Make the diagonal contain all 1's
            factor = matrix[i][i]
            for j in range(n):
                matrix[i][j] /= factor
                identity[i][j] /= factor
            # Make all rows below this one 0 in the current column
            for k in range(i + 1, n):
                factor = matrix[k][i]
                for j in range(n):
                    matrix[k][j] -= factor * matrix[i][j]
                    identity[k][j] -= factor * identity[i][j]
        # Back substitution to get upper triangular matrix to identity matrix
        for i in range(n - 1, -1, -1):
            for k in range(i - 1, -1, -1):
                factor = matrix[k][i]
                for j in range(n):
                    matrix[k][j] -= factor * matrix[i][j]
                    identity[k][j] -= factor * identity[i][j]
        return identity
    
    # Vandermonde matrix
    X = create_vandermonde_matrix(x, degree)
    
    # Transpose of Vandermonde matrix
    Xt = transpose(X)
    
    # Compute Xt * X
    XtX = matrix_multiply(Xt, X)
    
    # Compute the inverse of Xt * X
    XtX_inv = invert_matrix(XtX)
    
    # Compute Xt * y (this is the vector resulting from multiplying Xt by y)
    Xty = matrix_vector_multiply(Xt, y)
    
    # Compute the coefficients (XtX_inv * Xty)
    coefficients = matrix_vector_multiply(XtX_inv, Xty)
    
    return coefficients

def predict(coefficients, x):
    """Evaluates the polynomial at a given x using the coefficients."""
    return sum(c * (x ** i) for i, c in enumerate(coefficients))


# Example usage:
x = [0, 1, 2, 3, 4, 5]
y = [0, 0.8, 0.9, 0.1, -0.8, -1.0]

degree = 5  # Degree of the polynomial

# Compute the coefficients from polynomial regression
coefficients = polynomial_regression(x, y, degree)

# Predict new values
new_x = 5  # New x value to predict
predicted_y = predict(coefficients, new_x)

print(f'Coefficients of the polynomial fit: {coefficients}')
print(f'Predicted value at x = {new_x}: {predicted_y}')

def predict_new_position(positions):
    ROUNDING = 5
    
    x = [round(v[0], ROUNDING) for v in positions]
    y = [round(v[1], ROUNDING) for v in positions]

    diff_x = [x[i+1] - x[i] for i in range(0, len(x)-1)]
    diff_y = [y[i+1] - y[i] for i in range(0, len(y)-1)]
    avg_x = sum(diff_x)/len(diff_x)
    avg_y = sum(diff_y)/len(diff_y)
    new_x = x[-1] + avg_x
    new_y = y[-1] + avg_y

    return (new_x, new_y)


def predict_new_position_OLD(positions):
    ROUNDING = 0
    degree = 3
    bases_len = 5
    bases = [v for v in range(0, bases_len)]
    x = [round(v[0], ROUNDING) for v in positions]
    y = [round(v[1], ROUNDING) for v in positions]
    print("X: ", x)
    print("Y: ", y)
    x_regression = polynomial_regression(bases, x, degree)
    y_regression = polynomial_regression(bases, y, degree)
    new_x = predict(x_regression, bases_len)
    new_y = predict(y_regression, bases_len)
    print(predict(x_regression, 4))
    return (new_x, new_y)

#test_values = [(39.388240814208984, -18.625675201416016), (39.388240814208984, -18.625675201416016), (39.388240814208984, -18.625675201416016), (29.12446403503418, -0.9432782530784607), (33.186279296875, -4.639537811279297)]
test_values = [(33.265708923339844, -28.08803939819336), (33.463924407958984, -28.023414611816406), (33.463924407958984, -28.023412704467773), (33.46392059326172, -28.023414611816406), (32.288875579833984, -25.087141036987305)]
print(test_values)
test_values = test_values[:-1]
print("PREDICT: " ,predict_new_position(test_values))