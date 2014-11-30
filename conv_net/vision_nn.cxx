#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <fstream>
#include <vector>

#include "mpi.h"

//from TAO
#include "neural_networks/edge.hxx"
#include "neural_networks/vision_neural_network.hxx"

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
VisionNeuralNetwork *vs_nn;

void read_image_set(ifstream &infile, vector<char*> &images, vector<int> &classifications, int size, int count, int classification) {
    for (int i = 0; i < count; i++) {
        //cout << "reading image " << i << ", " << size << " bytes." << endl;
        char* image = new char[size];

        infile.read( image, sizeof(char) *size);
        images.push_back(image);
        classifications.push_back(classification);

        /*
        for (int j = 0; j < size; j++) {
            cout << " " << image[j];
        }
        cout << endl;
        */
    }
}

void read_images(string binary_filename, int &image_size, vector<char*> &images, vector<int> &classifications) {

    ifstream infile(binary_filename.c_str(), ios::in | ios::binary);
    if (infile.is_open()) {
        int initial_vals[4];
        infile.read( (char*)&initial_vals, sizeof(initial_vals) );

        int rowscols = initial_vals[0];
        int vals_per_pixel = initial_vals[1];
        int n_positive_images = initial_vals[2];
        int n_negative_images = initial_vals[3];

        //cout << "image size: " << rowscols << "x" << rowscols << "x" << vals_per_pixel << endl;
        //cout << "positive samples: " << n_positive_images << endl;
        //cout << "negative samples: " << n_negative_images << endl;

        image_size = rowscols * rowscols * vals_per_pixel;

        read_image_set(infile, images, classifications, image_size, n_positive_images, 1);
        read_image_set(infile, images, classifications, image_size, n_negative_images, -1);

        infile.close();
    } else {
        cerr << "Could not open '" << binary_filename << "' for reading." << endl;
    }
}


double objective_function(const vector<double> &parameters) {
    return vs_nn->objective_function(parameters);
}

double aco_objective_function(vector<Edge> &edges, vector<Edge> &recurrent_edges) {
    vs_nn->set_edges(edges);

    vector<double> min_bound(vs_nn->get_n_edges(), -1.5);
    vector<double> max_bound(vs_nn->get_n_edges(),  1.5);

    ParticleSwarm ps(min_bound, max_bound, arguments);

    //run EA
    ps.iterate(objective_function);

    //set the weights using the best found individual  
    //dont need to set recurrent edges because they're weights are always 1
    vector<double> global_best = ps.get_global_best();
    int current = 0;
    for (int i = 0; i < edges.size(); i++) {
        edges[i].weight = global_best[current];
        current++;
    }

    return ps.get_global_best_fitness();
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank, max_rank;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &max_rank);

    arguments = vector<string>(argv, argv + argc);

    vector<char*> images;
    vector<int> classifications;

    string binary_samples_filename;
    get_argument(arguments, "--samples_file", true, binary_samples_filename);

    int image_size;
    read_images(binary_samples_filename, image_size, images, classifications);

    if (rank == 0) cout << "read " << images.size() << " samples." << endl;

    int n_hidden_layers;
    int nodes_per_layer;
    get_argument(arguments, "--n_hidden_layers", true, n_hidden_layers);
    get_argument(arguments, "--nodes_per_layer", true, nodes_per_layer);

    vector<Edge> edges;
    for (int i = 0; i < image_size; i++) {
        for (int j = 0; j < nodes_per_layer; j++) {
            edges.push_back(Edge(0, 1, i, j));
        }
    }

    //bias
    for (int i = 0; i < nodes_per_layer; i++) {
        edges.push_back(Edge(0, 1, image_size, i));
    }


    for (int i = 1; i < n_hidden_layers; i++) {
        for (int j = 0; j < nodes_per_layer; j++) {
            for (int k = 0; k < nodes_per_layer; k++) {
                edges.push_back(Edge(i, i+1, j, k));
            }
        }

        //bias
        for (int j = 0; j < nodes_per_layer; j++) {
            edges.push_back(Edge(i, i+1, nodes_per_layer, j));
        }
    }

    for (int i = 0; i < nodes_per_layer; i++) {
        edges.push_back(Edge(n_hidden_layers, n_hidden_layers+1, i, 0));
    }
    //bias
    edges.push_back(Edge(n_hidden_layers, n_hidden_layers+1, nodes_per_layer, 0));

    if (rank == 0) cout << "image_size: " << image_size << endl;

    vs_nn = new VisionNeuralNetwork(image_size, images, classifications, n_hidden_layers, nodes_per_layer);
    vs_nn->set_edges(edges);

    vector<double> min_bound(vs_nn->get_n_edges(), -1.5);
    vector<double> max_bound(vs_nn->get_n_edges(),  1.5);

    if (rank == 0) cout << "number of parameters: " << vs_nn->get_n_edges() << endl;

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
        ps.go(objective_function);

    } else if (search_type.compare("de_mpi") == 0) {
        DifferentialEvolutionMPI de(min_bound, max_bound, arguments);
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

