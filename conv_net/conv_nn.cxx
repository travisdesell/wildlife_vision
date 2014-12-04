#include <iostream>
#include <iomanip>
#include <stdio.h>
#include <stdlib.h>
#include <fstream>
#include <vector>

#include "mpi.h"

//from TAO
#include "neural_networks/edge.hxx"
#include "neural_networks/convolutional_neural_network.hxx"

#include "mpi/mpi_ant_colony_optimization.hxx"
#include "mpi/mpi_particle_swarm.hxx"
#include "mpi/mpi_differential_evolution.hxx"

#include "asynchronous_algorithms/ant_colony_optimization.hxx"
#include "asynchronous_algorithms/neat.hxx"
#include "asynchronous_algorithms/particle_swarm.hxx"
#include "asynchronous_algorithms/differential_evolution.hxx"

#include "synchronous_algorithms/synchronous_newton_method.hxx"
#include "synchronous_algorithms/synchronous_gradient_descent.hxx"


//from undvc_common
#include "arguments.hxx"

using namespace std;

vector<string> arguments;
ConvolutionalNeuralNetwork *conv_nn;

void read_image_set(ifstream &infile, vector< vector< vector<char> > > &images, int size, int count, int classification) {
    for (int i = 0; i < count; i++) {
//        cout << "reading image " << i << ", " << size << " bytes." << endl;
        char* pixels = new char[size];

        infile.read( pixels, sizeof(char) * size);

        images[classification].push_back(vector<char>(pixels, pixels + size));

        delete pixels;

        /*
        for (int j = 0; j < size; j++) {
            cout << " " << (short) images[classification][images[classification].size() - 1][j];
        }
        cout << endl;
        */
    }
}

void read_images(string binary_filename, int &image_size, int &rowscols, vector< vector< vector<char> > > &images) {

    ifstream infile(binary_filename.c_str(), ios::in | ios::binary);

    if (infile.is_open()) {
        int initial_vals[3];
        infile.read( (char*)&initial_vals, sizeof(initial_vals) );

        int n_classes = initial_vals[0];
        rowscols = initial_vals[1];
        int vals_per_pixel = initial_vals[2];

        images = vector< vector< vector<char> > >(n_classes);

        //cout << "n_classes: " << n_classes << endl;
        //cout << "rowscols: " << rowscols << endl;
        //cout << "vals_per_pixel: " << vals_per_pixel << endl;

        vector<int> class_sizes(n_classes, 0);
        infile.read( (char*)&class_sizes[0], sizeof(int) * n_classes );


        image_size = rowscols * rowscols * vals_per_pixel;

        for (int i = 0; i < n_classes; i++) {
            //cout << "reading image set with " << class_sizes[i] << " files." << endl;
            read_image_set(infile, images, image_size, class_sizes[i], i);
        }

        infile.close();
    } else {
        cerr << "Could not open '" << binary_filename << "' for reading." << endl;
    }
}


double objective_function(const vector<double> &parameters) {
    return conv_nn->objective_function(parameters);
}

void print_statistics(const vector<double> &parameters) {
    return conv_nn->print_statistics(parameters);
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank, max_rank;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &max_rank);

    arguments = vector<string>(argv, argv + argc);

    vector< vector< vector<char> > > images;

    string binary_samples_filename;
    get_argument(arguments, "--samples_file", true, binary_samples_filename);

    int image_size, rowscols;
    read_images(binary_samples_filename, image_size, rowscols, images);
    if (rank == 0) {
        cout << "image_size: " << rowscols << "x" << rowscols << " = " << image_size << endl;

        cout << "read " << images.size() << " classes of samples." << endl;
        for (int i = 0; i < images.size(); i++) {
            cout << "    class " << setw(4) << i << ": " << images[i].size() << endl;
        }
    }

    vector<int> conv_sizes;
    vector<int> max_pool_sizes;
    get_argument_vector(arguments, "--convolutional_sizes", true, conv_sizes);
    get_argument_vector(arguments, "--max_pool_sizes", true, max_pool_sizes);

    if (conv_sizes.size() != max_pool_sizes.size()) {
        cerr << "ERROR: convolutional_sizes.size() [" << conv_sizes.size() << "] != max_pool_sizes.size() [" << max_pool_sizes.size() << "]" << endl;
        exit(1);
    }
    vector< pair<int,int> > layers;
    for (int i = 0; i < conv_sizes.size(); i++) {
        layers.push_back(pair<int, int>(conv_sizes[i], max_pool_sizes[i]));
    }


    int fc_size;
    get_argument(arguments, "--fully_connected_size", true, fc_size);

    bool quiet =false;
    if (rank != 0) quiet = true;
    conv_nn = new ConvolutionalNeuralNetwork(rowscols, rowscols, true, quiet, images, layers, fc_size);

    vector<double> min_bound(conv_nn->get_n_edges(), -2.0);
    vector<double> max_bound(conv_nn->get_n_edges(),  2.0);

    if (rank == 0) cout << "number of parameters: " << conv_nn->get_n_edges() << endl;

    string search_type;
    get_argument(arguments, "--search_type", true, search_type);


    if (search_type.compare("ps") == 0) {
        ParticleSwarm ps(min_bound, max_bound, arguments);
        ps.iterate(objective_function);

    } else if (search_type.compare("de") == 0) {
        DifferentialEvolution de(min_bound, max_bound, arguments);
        de.iterate(objective_function);

    } else if (search_type.compare("ps_mpi") == 0) {
        ParticleSwarmMPI ps(min_bound, max_bound, arguments);
        ps.set_print_statistics(print_statistics);
        ps.go(objective_function);

    } else if (search_type.compare("de_mpi") == 0) {
        DifferentialEvolutionMPI de(min_bound, max_bound, arguments);
        de.set_print_statistics(print_statistics);
        de.go(objective_function);

    } else if (search_type.compare("snm") == 0 || search_type.compare("gd") == 0 || search_type.compare("cgd") == 0) {
        string starting_point_s;
        vector<double> starting_point(min_bound.size(), 0);

        if (get_argument(arguments, "--starting_point", false, starting_point_s)) {
            cout << "#starting point: '" << starting_point_s << "'" << endl;
            string_to_vector(starting_point_s, starting_point);
        } else {
            for (unsigned int i = 0; i < min_bound.size(); i++) {
                starting_point[i] = min_bound[i] + ((max_bound[i] - min_bound[i]) * drand48());
            }
        }

        vector<double> step_size(min_bound.size(), 0.001);

        if (search_type.compare("snm") == 0) {
            synchronous_newton_method(arguments, objective_function, starting_point, step_size);
        } else if (search_type.compare("gd") == 0) {
            vector<double> final_parameters;
            double final_fitness;
            synchronous_gradient_descent(arguments, objective_function, starting_point, step_size, final_parameters, final_fitness);
        } else if (search_type.compare("cgd") == 0) {
            synchronous_conjugate_gradient_descent(arguments, objective_function, starting_point, step_size);
        }

    } else {
        fprintf(stderr, "Improperly specified search type: '%s'\n", search_type.c_str());
        fprintf(stderr, "Possibilities are:\n");
        fprintf(stderr, "    de     -       differential evolution\n");
        fprintf(stderr, "    ps     -       particle swarm optimization\n");
        fprintf(stderr, "    de_mpi -       asynchronous differential evolution over MPI\n");
        fprintf(stderr, "    ps_mpi -       asynchronous particle swarm optimization over MPI\n");
        fprintf(stderr, "    snm    -       synchronous newton method\n");
        fprintf(stderr, "    gd     -       gradient descent\n");
        fprintf(stderr, "    cgd    -       conjugate gradient descent\n");

        exit(0);
    }

    return 0;
}

